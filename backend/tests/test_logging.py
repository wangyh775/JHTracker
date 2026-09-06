"""
backend/tests/test_logging.py - 日志与审计追踪体系单元与契约测试
"""

import os
import io
import time
import logging
import tempfile
from pathlib import Path
import pytest
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.config import LoggingConfig, config
from src.logger import (
    setup_logging,
    get_logger,
    SensitiveDataFilter,
    audit_mcp_tool,
    PHONE_PATTERN,
    EMAIL_PATTERN
)


def test_sensitive_data_filter():
    """测试敏感数据过滤器能正确脱敏手机号、邮箱和密钥"""
    f = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User phone: 13812345678, email: jobseeker@example.com, token: Bearer eyJhbGciOiJIUzI1NiJ9",
        args=(),
        exc_info=None
    )
    res = f.filter(record)
    assert res is True
    assert "138****5678" in record.msg
    assert "13812345678" not in record.msg
    assert "j***@example.com" in record.msg
    assert "jobseeker@example.com" not in record.msg
    assert "Bearer [REDACTED]" in record.msg


def test_logger_file_and_console_output():
    """测试日志成功写入临时文件，且格式规范"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_log_dir = Path(temp_dir) / "logs"
        cfg = LoggingConfig(
            log_dir=temp_log_dir,
            log_file_name="test.log",
            log_level="DEBUG",
            console_enabled=True,
            file_enabled=True
        )
        setup_logging(cfg)
        logger = get_logger("test.file_output")

        test_msg = "Test message for JHTracker logging verification"
        logger.info(test_msg)

        # 确保 handler 刷新并关闭，释放 Windows 文件句柄
        for h in list(logging.getLogger().handlers):
            h.flush()
            h.close()
            logging.getLogger().removeHandler(h)

        log_file = cfg.log_file_path
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert test_msg in content
        assert "[INFO]" in content
        assert "[test.file_output]" in content


@pytest.mark.asyncio
async def test_audit_mcp_tool_decorator_async():
    """测试 @audit_mcp_tool 对异步函数的入参、耗时和异常捕获"""
    captured_logs = []

    class MockHandler(logging.Handler):
        def emit(self, record):
            captured_logs.append(self.format(record))

    handler = MockHandler()
    audit_logger = logging.getLogger("jhtracker.mcp.audit")
    audit_logger.addHandler(handler)

    @audit_mcp_tool(tool_name="test_tool")
    async def sample_async_tool(query: str, secret_token: str):
        return f"result for {query}"

    res = await sample_async_tool("python", secret_token="abc123456")
    assert res == "result for python"

    log_text = "\n".join(captured_logs)
    assert "START tool=test_tool" in log_text
    assert "[REDACTED]" in log_text
    assert "abc123456" not in log_text
    assert "SUCCESS tool=test_tool" in log_text
    assert "duration_ms=" in log_text

    # 测试异常流程
    @audit_mcp_tool(tool_name="failing_tool")
    async def failing_async_tool():
        raise ValueError("Simulated tool error")

    with pytest.raises(ValueError):
        await failing_async_tool()

    log_text_fail = "\n".join(captured_logs)
    assert "FAIL tool=failing_tool" in log_text_fail
    assert "ValueError: Simulated tool error" in log_text_fail


@pytest.mark.asyncio
async def test_fastapi_logging_middleware_and_unhandled_exception():
    """测试 FastAPI 访问日志中间件注入 X-Request-ID、X-Process-Time 以及全局异常处理"""
    from httpx import AsyncClient, ASGITransport
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 正常请求
        resp = await client.get("/api/jobs?limit=1")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert "X-Process-Time" in resp.headers

        # 客户端自带 Request-ID
        custom_req_id = "test-client-req-999"
        resp_custom = await client.get("/api/jobs?limit=1", headers={"X-Request-ID": custom_req_id})
        assert resp_custom.status_code == 200
        assert resp_custom.headers["X-Request-ID"] == custom_req_id

        # 触发全局未捕获异常
        from unittest.mock import patch
        with patch.object(app.state.job_repo, "search_jobs", side_effect=RuntimeError("Simulated DB Crash")):
            resp_err = await client.get("/api/jobs?limit=1")
            assert resp_err.status_code == 500
            data = resp_err.json()
            assert data["error"] == "Internal Server Error"
            assert "request_id" in data
            assert resp_err.headers["X-Request-ID"] == data["request_id"]


def test_logger_graceful_fallback(tmp_path):
    """测试当指定只读或非法日志目录时，logger 优雅降级并输出警告而不导致应用崩溃"""
    from src.logger import setup_logging
    from src.config import LoggingConfig
    from unittest.mock import patch

    custom_cfg = LoggingConfig(log_dir=tmp_path / "protected", console_output=True)

    with patch("src.logger.TimedRotatingFileHandler", side_effect=PermissionError("Permission denied")):
        # setup_logging 应当捕获异常并降级，不抛出致命错误
        setup_logging(cfg=custom_cfg)


