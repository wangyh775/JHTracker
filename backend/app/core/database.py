from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
import os

# Project Root data directory (sharing data with v1.0 Flask and automation scripts)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "tracker.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 异步引擎配置，开启 WAL 与 busy_timeout
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"timeout": 10}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    # 强制设置 SQLite PRAGMA journal_mode=WAL
    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.exec_driver_sql("PRAGMA busy_timeout=5000;")
        await conn.run_sync(Base.metadata.create_all)
