import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.app.core.database import init_db
from backend.app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动初始化 DB 与 WAL PRAGMA
    await init_db()
    yield

app = FastAPI(
    title="Career Tracker v2.0",
    description="Personal Career OS: Vue 3 SPA + Async FastAPI Backend",
    version="2.0.0",
    lifespan=lifespan
)

# 允许跨域以便本地开发 Vite (5173) 联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)

# 挂载前端打包后的静态资源 (SPA 托管)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "dist")
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 如果请求的不是 api 路由，默认返回 index.html
        if not full_path.startswith("api"):
            index_file = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
        return {"detail": "Not Found"}
