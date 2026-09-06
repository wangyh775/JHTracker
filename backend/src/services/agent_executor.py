import os
import shutil
import asyncio
import re
import json
from typing import Dict, Any, List, Optional
import httpx
from src.logger import get_logger

logger = get_logger("jhtracker.service.agent_executor")

ANSI_ESCAPE_PATTERN = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

class AgentExecutor:
    """
    本地智能体 CLI 探活、标准 OpenAI 兼容 HTTP 直连及子进程管道执行器。
    一等公民支持: custom_api (直连大模型), opencode, hermes 以及内置启发式规则引擎 (builtin)。
    """

    @classmethod
    def detect_available_agents(cls, custom_llm_configured: bool = False) -> Dict[str, Any]:
        """
        探测本地可用的智能体执行器。
        优先顺序: custom_api (若配置/可用) > hermes > opencode > builtin
        """
        agents: List[Dict[str, Any]] = []

        # 1. 始终提供 / 挂载自定义 OpenAI 兼容接口直连
        agents.append({
            "id": "custom_api",
            "name": "自定义/本地 LLM (OpenAI兼容API)",
            "available": True,
            "path": None,
            "description": "直连本地 (如 localhost:8045/v1, Ollama, LM Studio) 或云端大模型，秒级极速响应"
        })

        # 2. 探测 hermes
        hermes_bin = shutil.which("hermes") or shutil.which("hermes.exe")
        if not hermes_bin:
            default_hermes = os.path.expanduser("~\\AppData\\Local\\hermes\\bin\\hermes.exe")
            if os.path.exists(default_hermes):
                hermes_bin = default_hermes

        if hermes_bin:
            agents.append({
                "id": "hermes",
                "name": "Hermes Agent",
                "available": True,
                "path": hermes_bin,
                "description": "本地 Hermes 智能体 (One-shot 管道模式)"
            })

        # 3. 探测 opencode
        opencode_bin = shutil.which("opencode") or shutil.which("opencode.cmd")
        if opencode_bin:
            agents.append({
                "id": "opencode",
                "name": "OpenCode CLI",
                "available": True,
                "path": opencode_bin,
                "description": "本地 OpenCode 智能体 CLI"
            })

        # 4. 始终挂载内置启发式规则引擎
        agents.append({
            "id": "builtin",
            "name": "内置启发式规则引擎 (离线/秒级)",
            "available": True,
            "path": None,
            "description": "基于 FTS 与 STAR 模式的轻量级纯本地算法，无外部依赖"
        })

        # 推荐逻辑
        recommended = "custom_api" if custom_llm_configured else "builtin"
        if not custom_llm_configured:
            for candidate in ["hermes", "opencode"]:
                if any(a["id"] == candidate for a in agents):
                    recommended = candidate
                    break

        return {
            "recommended": recommended,
            "agents": agents
        }

    @classmethod
    async def execute_via_http(
        cls,
        prompt: str,
        base_url: str,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.3,
        timeout: float = 60.0
    ) -> Optional[Dict[str, Any]]:
        """
        直接通过 HTTP 调用 OpenAI 兼容的 /chat/completions 接口，零子进程开销，秒级响应。
        """
        norm_base = (base_url or "").rstrip("/")
        if not norm_base.endswith("/chat/completions"):
            endpoint = f"{norm_base}/chat/completions"
        else:
            endpoint = norm_base

        headers = {
            "Content-Type": "application/json"
        }
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的 ATS 招聘简历与职场优化专家。你的所有回答必须严格输出为合法的单个 JSON 代码块，严禁包含任何多余的前言、解释说明或外部 Markdown 杂音。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "stream": False
        }

        logger.info(f"Dispatching task to custom LLM API endpoint: {endpoint} (model={model}, timeout={timeout}s)")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"Custom LLM API returned status {resp.status_code}: {resp.text[:200]}")
                    return None

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed_json = cls._extract_json(content)
                if parsed_json:
                    parsed_json["_engine_used"] = f"LLM 直连 ({model})"
                    return parsed_json

                logger.warning(f"Failed to parse structured JSON from custom LLM response. Length={len(content)}")
                return None
        except Exception as e:
            logger.warning(f"Custom LLM API request failed: {e}")
            return None

    @classmethod
    async def test_connection(
        cls,
        base_url: str,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        轻量级探测 OpenAI 兼容端点是否连通且可用。
        发送一条极简打招呼请求，返回连通状态、延迟以及模型返回摘要。
        """
        import time
        norm_base = (base_url or "").rstrip("/")
        if not norm_base:
            return {"success": False, "error": "Base URL 不能为空"}

        if not norm_base.endswith("/chat/completions"):
            endpoint = f"{norm_base}/chat/completions"
        else:
            endpoint = norm_base

        headers = {
            "Content-Type": "application/json"
        }
        if api_key and api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"

        payload = {
            "model": model or "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": "Hi, reply 'OK'."
                }
            ],
            "max_tokens": 10,
            "stream": False
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                latency_ms = int((time.time() - start_time) * 1000)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return {
                        "success": True,
                        "latency_ms": latency_ms,
                        "model": model,
                        "reply": content[:60] if content else "OK",
                        "message": f"连接成功！延迟: {latency_ms}ms"
                    }
                else:
                    err_hint = ""
                    if resp.status_code == 401:
                        err_hint = " (鉴权失败，请检查 API Key 是否正确)"
                    elif resp.status_code == 404:
                        err_hint = " (端点未找到，请检查 Base URL 是否正确，如是否需包含 /v1)"
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "error": f"HTTP {resp.status_code}{err_hint}: {resp.text[:150]}"
                    }
        except httpx.ConnectError:
            return {"success": False, "error": f"无法连接到目标服务，请检查地址是否正确或服务是否启动: {base_url}"}
        except httpx.TimeoutException:
            return {"success": False, "error": f"连接超时 (>{timeout}s)，请检查服务网络或提高响应超时"}
        except Exception as e:
            return {"success": False, "error": f"连接发生异常: {str(e)}"}

    @classmethod
    async def execute_prompt(
        cls,
        prompt: str,
        engine: str = "auto",
        timeout: float = 60.0,
        llm_config: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        通过选定的引擎执行 Prompt 并解析返回的结构化 JSON。
        若执行失败或超时，返回 None (调用方自动降级为内置规则)。
        """
        target_engine = engine.lower() if engine else "auto"

        # 测试环境下，如果未显式 mock 且是 auto，默认走 builtin 保证毫秒级单元测试速度与幂等性
        if os.environ.get("PYTEST_CURRENT_TEST") and target_engine == "auto":
            logger.info("Running under pytest environment with engine='auto', routing directly to builtin.")
            return None

        # 如果指定了 custom_api 或者在 auto 下提供了 llm_config 且配置有效
        if target_engine in ("custom_api", "llm", "api") or (
            target_engine == "auto" and llm_config and getattr(llm_config, "base_url", None)
        ):
            base_url = getattr(llm_config, "base_url", "http://127.0.0.1:8045/v1") if llm_config else "http://127.0.0.1:8045/v1"
            api_key = getattr(llm_config, "api_key", "") if llm_config else ""
            model = getattr(llm_config, "model", "claude-3-5-sonnet-20241022") if llm_config else "claude-3-5-sonnet-20241022"
            temp = getattr(llm_config, "temperature", 0.3) if llm_config else 0.3

            res = await cls.execute_via_http(
                prompt=prompt,
                base_url=base_url,
                api_key=api_key,
                model=model,
                temperature=temp,
                timeout=timeout
            )
            if res:
                return res
            # 如果显式要求 custom_api 且失败，则不再盲目调用 CLI，避免挂起
            if target_engine in ("custom_api", "llm", "api"):
                logger.warning("Custom LLM API execution failed, falling back to builtin.")
                return None

        detection = cls.detect_available_agents(custom_llm_configured=bool(llm_config))
        available_map = {a["id"]: a for a in detection["agents"]}

        if target_engine == "auto":
            target_engine = detection["recommended"]

        # 内置引擎不需要调子进程，直接返回 None 让上层走规则引擎
        if target_engine == "builtin" or target_engine not in available_map:
            logger.info(f"Engine selected: {target_engine}, routing to builtin rule engine.")
            return None

        agent_info = available_map[target_engine]
        bin_path = agent_info.get("path")
        if not bin_path or not os.path.exists(bin_path):
            logger.warning(f"Binary for agent {target_engine} not found at {bin_path}, falling back to builtin.")
            return None

        cmd: List[str] = []
        if target_engine == "hermes":
            cmd = [bin_path, "-z", prompt, "--ignore-rules"]
        elif target_engine == "opencode":
            if os.name == "nt" and bin_path.lower().endswith((".cmd", ".bat")):
                cmd = ["cmd.exe", "/c", bin_path, "run", prompt]
            else:
                cmd = [bin_path, "run", prompt]
        else:
            logger.warning(f"Unsupported CLI engine {target_engine}")
            return None

        logger.info(f"Dispatching task to local agent CLI: {target_engine} (timeout={timeout}s)")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=getattr(asyncio.subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            raw_output = stdout_bytes.decode("utf-8", errors="ignore")
            clean_output = ANSI_ESCAPE_PATTERN.sub("", raw_output).strip()

            if process.returncode != 0:
                logger.warning(f"Agent CLI {target_engine} exited with code {process.returncode}: {clean_output[:200]}")

            parsed_json = cls._extract_json(clean_output)
            if parsed_json:
                parsed_json["_engine_used"] = agent_info["name"]
                return parsed_json
            
            logger.warning(f"Failed to parse structured JSON from {target_engine} output. Raw length={len(clean_output)}")
            return None

        except asyncio.TimeoutError:
            logger.warning(f"Agent CLI {target_engine} execution timed out after {timeout}s.")
            try:
                process.kill()
            except Exception:
                pass
            return None
        except Exception as e:
            logger.error(f"Error executing agent CLI {target_engine}: {e}", exc_info=True)
            return None

    @classmethod
    def _extract_json(cls, text: str) -> Optional[Dict[str, Any]]:
        """从杂乱文本中鲁棒解析 JSON"""
        if not text:
            return None

        # 1. 尝试找 ```json ... ```
        codeblock_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if codeblock_match:
            try:
                return json.loads(codeblock_match.group(1))
            except Exception:
                pass

        # 2. 尝试提取首尾最近的 { ... }
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx : end_idx + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        return None
