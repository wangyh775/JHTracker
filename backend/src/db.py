from contextlib import asynccontextmanager
import aiosqlite
from pathlib import Path
from typing import Optional, AsyncGenerator
from src.config import config

PUBLIC_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    industry TEXT,
    type_tags TEXT,
    batch TEXT,
    education_req TEXT,
    target_grad_year TEXT,
    salary_range TEXT,
    publish_date TEXT NOT NULL,
    deadline TEXT,
    detail_url TEXT,
    referral_code TEXT,
    description TEXT,
    source_site TEXT DEFAULT 'default',
    popular_level INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_publish_date ON jobs(publish_date);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);

CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
    title,
    company,
    location,
    description,
    content='jobs',
    content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id TEXT PRIMARY KEY,
    source_site TEXT NOT NULL,
    category TEXT,
    items_fetched INTEGER DEFAULT 0,
    items_inserted INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    error_message TEXT,
    started_at TEXT DEFAULT (datetime('now', 'localtime')),
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_started ON sync_logs(started_at);
"""

USER_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_positions TEXT,
    target_cities TEXT,
    target_types TEXT,
    target_grad_year TEXT,
    time_filter_config TEXT,
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS resumes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT DEFAULT 'GENERAL',
    file_path TEXT NOT NULL,
    content_md TEXT,
    target_job_id TEXT,
    parsed_skills TEXT,
    keywords_matrix TEXT,
    is_default INTEGER DEFAULT 0,
    version_type TEXT DEFAULT 'ORIGINAL',
    parent_resume_id TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    resume_id TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING_APPLY',
    apply_date TEXT,
    schedule_time TEXT,
    channel TEXT,
    account_memo TEXT,
    interview_notes TEXT,
    salary_offered TEXT,
    priority INTEGER DEFAULT 0,
    match_score REAL,
    recommend_reason TEXT,
    is_archived INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
-- Note: idx_applications_archived is created in init_user_db after column migration

CREATE TABLE IF NOT EXISTS application_timeline (
    id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    note TEXT,
    changed_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS recommendation_feedback (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    match_score REAL,
    recommend_reason TEXT,
    action TEXT NOT NULL,
    reject_reasons TEXT,
    feedback_time TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS feature_weights (
    feature_key TEXT PRIMARY KEY,
    feature_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    accept_count INTEGER DEFAULT 0,
    reject_count INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS agent_pushes (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    agent_name TEXT DEFAULT 'JobSourcingAgent',
    recommend_reason TEXT NOT NULL,
    match_score REAL DEFAULT 0.95,
    pushed_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS user_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

async def init_public_db(db_path: Optional[Path] = None):
    path = Path(db_path) if db_path else config.public_db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA busy_timeout = 5000")
        await db.executescript(PUBLIC_SCHEMA)
        await db.commit()

async def init_user_db(db_path: Optional[Path] = None):
    path = Path(db_path) if db_path else config.user_db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 5000")
        # Step 1: Run table definitions (without index on newly migrated columns)
        await db.executescript(USER_SCHEMA)
        # Step 2: Run schema migrations for existing tables
        try:
            await db.execute("ALTER TABLE resumes ADD COLUMN is_default INTEGER DEFAULT 0")
        except Exception:
            pass  # Already exists
        try:
            await db.execute("ALTER TABLE resumes ADD COLUMN version_type TEXT DEFAULT 'ORIGINAL'")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE resumes ADD COLUMN parent_resume_id TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE resumes ADD COLUMN keywords_matrix TEXT")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE applications ADD COLUMN is_archived INTEGER DEFAULT 0")
        except Exception:
            pass
        # Step 3: Run indexes that depend on migrated columns
        try:
            await db.execute("CREATE INDEX IF NOT EXISTS idx_applications_archived ON applications(is_archived)")
        except Exception:
            pass
        # Step 4: Ensure user_settings table exists
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
        except Exception:
            pass
        await db.commit()

async def init_all_databases():
    await init_public_db()
    await init_user_db()

@asynccontextmanager
async def get_public_db(db_path: Optional[Path] = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    path = db_path or config.public_db_path
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA busy_timeout = 5000")
        db.row_factory = aiosqlite.Row
        yield db

@asynccontextmanager
async def get_user_db(db_path: Optional[Path] = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    path = db_path or config.user_db_path
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA busy_timeout = 5000")
        db.row_factory = aiosqlite.Row
        yield db
