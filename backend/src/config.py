import os
from pathlib import Path
from pydantic import BaseModel, Field

class LoggingConfig(BaseModel):
    # Log directory inside private user space
    log_dir: Path = Field(default_factory=lambda: Path(os.path.expanduser("~/.JHTracker/logs")))
    log_file_name: str = "jhtracker.log"
    log_level: str = "INFO"
    rotation_when: str = "midnight"
    backup_count: int = 14
    console_enabled: bool = True
    file_enabled: bool = True

    @property
    def log_file_path(self) -> Path:
        return self.log_dir / self.log_file_name

class AppConfig(BaseModel):
    # Application version (reads from root VERSION file with fallback)
    version: str = Field(default_factory=lambda: AppConfig._load_version())

    # Base user directory for private data isolation
    user_data_dir: Path = Field(default_factory=lambda: Path(os.path.expanduser("~/.JHTracker")))
    # Public shared data directory in repo root
    public_data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data")

    # Logging config
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Database file names
    user_db_name: str = "user_data.db"
    public_db_name: str = "public_jobs.db"

    # Time filtering & recommendation defaults
    default_time_window_months: int = 3
    default_min_match_score: float = 0.60

    # HITL Feature Weight Params
    accept_reward: float = 0.15
    company_reject_penalty: float = 0.05
    tag_reject_penalty: float = 0.70
    min_weight_floor: float = 0.10
    max_weight_ceiling: float = 2.00

    @staticmethod
    def _load_version() -> str:
        version_file = Path(__file__).resolve().parent.parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return "0.1.0"

    @property
    def user_db_path(self) -> Path:
        return self.user_data_dir / self.user_db_name

    @property
    def public_db_path(self) -> Path:
        return self.public_data_dir / self.public_db_name

    @property
    def resumes_dir(self) -> Path:
        return self.user_data_dir / "resumes"

    def ensure_directories(self):
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.public_data_dir.mkdir(parents=True, exist_ok=True)
        self.resumes_dir.mkdir(parents=True, exist_ok=True)
        self.logging.log_dir.mkdir(parents=True, exist_ok=True)

config = AppConfig()
config.ensure_directories()
settings = config
