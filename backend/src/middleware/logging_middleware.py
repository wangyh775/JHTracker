"""
backend/src/middleware/logging_middleware.py - HTTP 访问日志与耗时追踪中间件
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from src.logger import get_logger

access_logger = get_logger("jhtracker.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP 访问日志中间件：
    1. 为每个请求生成或透传 X-Request-ID
    2. 记录请求进入与响应完成日志（Method, Path, IP, Status Code, 耗时 ms）
    3. 在响应头中附加 X-Request-ID 与 X-Process-Time
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # 挂载到 request.state 方便下游业务或异常处理器读取
        request.state.request_id = request_id

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        try:
            response: Response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            status_code = response.status_code
            log_msg = f"{method} {path} status={status_code} ip={client_ip} duration_ms={duration_ms:.2f} req_id={request_id}"

            if status_code >= 500:
                access_logger.error(log_msg)
            elif status_code >= 400:
                access_logger.warning(log_msg)
            else:
                access_logger.info(log_msg)

            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            access_logger.error(
                f"{method} {path} status=500 ip={client_ip} duration_ms={duration_ms:.2f} req_id={request_id} error={type(exc).__name__}: {str(exc)}",
                exc_info=True
            )
            # 在中间件内部捕获未处理异常，直接返回标准的 500 JSON 响应，确保头部包含 X-Request-ID 和 X-Process-Time
            return FastAPIJSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred while processing your request.",
                    "request_id": request_id
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{duration_ms:.2f}ms"
                }
            )
