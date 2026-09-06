"""
backend/src/logger.py - 统一日志系统核心模块
提供控制台与文件轮转输出、敏感信息脱敏过滤器、MCP 工具审计装饰器。
"""

import os
import sys
import re
import time
import functools
import inspect
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional, Callable, Any

from src.config import config, LoggingConfig

# 敏感信息过滤正则定义
PHONE_PATTERN = re.compile(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)")
EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*(@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)([A-Za-z0-9\-._~+/]+=*)")
TOKEN_PATTERN = re.compile(r"(?i)\b(api[_-]?key|secret|password)(\s*[:=]\s*['\"]?)([^'\"\s,\}]+)(['\"]?)")


class SensitiveDataFilter(logging.Filter):
    """
    敏感数据脱敏过滤器：
    对手机号、邮箱、Authorization/Bearer Token、API Key 等进行自动掩码。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.msg, str):
            record.msg = str(record.msg)

        msg = record.msg
        # 1. 手机号脱敏: 13812345678 -> 138****5678
        msg = PHONE_PATTERN.sub(r"\1****\2", msg)
        # 2. 邮箱脱敏: user@example.com -> u***@example.com
        msg = EMAIL_PATTERN.sub(r"\1***\2", msg)
        # 3. Bearer Token 脱敏
        msg = BEARER_PATTERN.sub(r"\1[REDACTED]", msg)
        # 4. Token/Secret/Password 脱敏
        msg = TOKEN_PATTERN.sub(r"\1\2[REDACTED]\4", msg)

        record.msg = msg

        # 如果 args 包含字符串参数也脱敏
        if record.args:
            if isinstance(record.args, dict):
                scrubbed_args = {}
                for k, v in record.args.items():
                    if isinstance(v, str):
                        v_sub = PHONE_PATTERN.sub(r"\1****\2", v)
                        v_sub = EMAIL_PATTERN.sub(r"\1***\2", v_sub)
                        v_sub = BEARER_PATTERN.sub(r"\1[REDACTED]", v_sub)
                        v_sub = TOKEN_PATTERN.sub(r"\1\2[REDACTED]\4", v_sub)
                        scrubbed_args[k] = v_sub
                    else:
                        scrubbed_args[k] = v
                record.args = scrubbed_args
            elif isinstance(record.args, tuple):
                scrubbed_tuple = []
                for v in record.args:
                    if isinstance(v, str):
                        v_sub = PHONE_PATTERN.sub(r"\1****\2", v)
                        v_sub = EMAIL_PATTERN.sub(r"\1***\2", v_sub)
                        v_sub = BEARER_PATTERN.sub(r"\1[REDACTED]", v_sub)
                        v_sub = TOKEN_PATTERN.sub(r"\1\2[REDACTED]\4", v_sub)
                        scrubbed_tuple.append(v_sub)
                    else:
                        scrubbed_tuple.append(v)
                record.args = tuple(scrubbed_tuple)

        return True


class ISO8601Formatter(logging.Formatter):
    """
    统一 ISO-8601 时间格式化日志输出器
    """
    default_msec_format = "%s.%03d"

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%dT%H:%M:%S", ct)
            s = f"{t}.{int(record.msecs):03d}Z"
        return s


_logging_initialized = False


def setup_logging(cfg: Optional[LoggingConfig] = None) -> None:
    """
    初始化全局日志系统配置（幂等）：
    1. 配置根日志器与格式
    2. 注册控制台 Handler
    3. 注册文件轮转 Handler（支持降级回退）
    4. 附加敏感数据脱敏过滤器
    """
    global _logging_initialized
    if cfg is None:
        cfg = config.logging

    log_level = getattr(logging, cfg.log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除旧的 Handlers 避免重复打印
    root_logger.handlers.clear()

    formatter = ISO8601Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [thread:%(thread)d] %(message)s"
    )
    sensitive_filter = SensitiveDataFilter()

    # 1. 控制台 Handler
    if cfg.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)

    # 2. 文件轮转 Handler
    if cfg.file_enabled:
        try:
            cfg.log_dir.mkdir(parents=True, exist_ok=True)
            log_path = cfg.log_file_path

            file_handler = TimedRotatingFileHandler(
                filename=str(log_path),
                when=cfg.rotation_when,
                interval=1,
                backupCount=cfg.backup_count,
                encoding="utf-8",
                delay=True
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(sensitive_filter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # 优雅降级：仅使用控制台日志，不让服务启动崩溃
            sys.stderr.write(f"[WARN] Failed to initialize file logger at {cfg.log_dir}: {e}. Falling back to console only.\n")

    _logging_initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    获取指定模块名称的 Logger 实例
    """
    global _logging_initialized
    if not _logging_initialized:
        setup_logging()
    return logging.getLogger(name)


def sanitize_value(val: Any) -> Any:
    """
    递归对字典或对象进行敏感字段脱敏
    """
    if isinstance(val, dict):
        sanitized = {}
        for k, v in val.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ["token", "secret", "password", "auth", "key"]):
                sanitized[k] = "[REDACTED]"
            elif k_lower in ["phone", "mobile", "telephone"] and isinstance(v, str):
                sanitized[k] = PHONE_PATTERN.sub(r"\1****\2", v)
            elif k_lower in ["email", "mail"] and isinstance(v, str):
                sanitized[k] = EMAIL_PATTERN.sub(r"\1***\2", v)
            elif isinstance(v, (dict, list)):
                sanitized[k] = sanitize_value(v)
            elif isinstance(v, str) and len(v) > 200:
                sanitized[k] = v[:200] + "...[TRUNCATED]"
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(val, list):
        return [sanitize_value(item) for item in val[:10]]
    elif isinstance(val, str) and len(val) > 200:
        return val[:200] + "...[TRUNCATED]"
    return val


def audit_mcp_tool(tool_name: Optional[str] = None):
    """
    MCP 工具调用的审计装饰器：
    记录工具调用名、安全参数、耗时及执行结果/异常。
    """
    def decorator(func: Callable):
        actual_tool_name = tool_name or func.__name__
        audit_logger = get_logger("jhtracker.mcp.audit")

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                clean_kwargs = sanitize_value(kwargs)
                audit_logger.info(
                    f"START tool={actual_tool_name} args={clean_kwargs}"
                )
                try:
                    res = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    audit_logger.info(
                        f"SUCCESS tool={actual_tool_name} duration_ms={duration_ms:.2f}"
                    )
                    return res
                except Exception as ex:
                    duration_ms = (time.time() - start_time) * 1000
                    audit_logger.error(
                        f"FAIL tool={actual_tool_name} duration_ms={duration_ms:.2f} error={type(ex).__name__}: {str(ex)}"
                    )
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                clean_kwargs = sanitize_value(kwargs)
                audit_logger.info(
                    f"START tool={actual_tool_name} args={clean_kwargs}"
                )
                try:
                    res = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    audit_logger.info(
                        f"SUCCESS tool={actual_tool_name} duration_ms={duration_ms:.2f}"
                    )
                    return res
                except Exception as ex:
                    duration_ms = (time.time() - start_time) * 1000
                    audit_logger.error(
                        f"FAIL tool={actual_tool_name} duration_ms={duration_ms:.2f} error={type(ex).__name__}: {str(ex)}"
                    )
                    raise
            return sync_wrapper

    return decorator
