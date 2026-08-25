import os
import sys
import uvicorn

if __name__ == "__main__":
    # 确保当前目录在 sys.path 中
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    # 启动 FastAPI 服务，监听 8000 端口
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
