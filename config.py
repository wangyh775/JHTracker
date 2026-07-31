"""集中配置：路径、密钥、分页大小等。

所有用户可定制项均支持环境变量覆盖，默认值保证开箱即用。
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('JH_DATA_DIR', os.path.join(BASE_DIR, 'data'))
DB_PATH = os.path.join(DATA_DIR, 'tracker.db')
RESUME_DIR = os.path.join(DATA_DIR, 'resumes')

# 用户简历画像，供 AI 评分使用（Markdown 纯文本）
PROFILE_FILE = os.path.join(DATA_DIR, 'profile.md')


def _load_or_create_secret_key():
    """从 data/.secret_key 加载持久化密钥，不存在则随机生成并写回。

    避免每次重启 session 失效；优先尊重环境变量 SECRET_KEY。
    """
    sk = os.environ.get('SECRET_KEY')
    if sk:
        return sk
    key_file = os.path.join(DATA_DIR, '.secret_key')
    try:
        with open(key_file, 'r') as f:
            return f.read().strip()
    except (OSError, IOError):
        import secrets
        new_key = secrets.token_hex(32)
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(key_file, 'w') as f:
                f.write(new_key)
        except OSError:
            # data 目录不可写时退化为内存随机（重启失效但能跑）
            pass
        return new_key


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = _load_or_create_secret_key()

    # 公司清单数据源：默认 career_data/，可由环境变量覆盖
    CAREER_DIR = os.environ.get('CAREER_DIR', os.path.join(BASE_DIR, 'career_data'))
    COMPANY_FILE_PATTERN = '企业清单_{source}_*.md'

    # 分页
    PER_PAGE_COMPANIES = 40
    PER_PAGE_APPLICATIONS = 30
    PER_PAGE_NOTES = 30

    # 简历上传
    UPLOAD_FOLDER = RESUME_DIR
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB
    ALLOWED_RESUME_EXT = {'pdf', 'docx', 'doc'}

    # AI 评分配置（可选）
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'openai')  # openai / anthropic
    AI_MODEL = os.environ.get('AI_MODEL', 'Hermes')
    AI_API_KEY = os.environ.get('OPENAI_API_KEY')  # 9Router / 组合模型使用 OpenAI 兼容接口
    AI_BASE_URL = os.environ.get('AI_BASE_URL', 'http://localhost:20128/v1')

    # 投递归档配置（可被 data/settings.json 覆盖）
    ARCHIVE_STALE_DAYS = int(os.environ.get('JH_ARCHIVE_STALE_DAYS', 15))
    ARCHIVE_AUTO_ENABLED = os.environ.get('JH_ARCHIVE_AUTO', '1') == '1'


class DevConfig(Config):
    """开发环境配置：开启调试，便于排查问题。"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # 设 True 会打印所有 SQL，按需开启


class ProdConfig(Config):
    """生产环境配置：关闭调试，仅本机访问场景下仍保持稳健默认值。"""
    DEBUG = False


# 按环境变量选择配置：FLASK_ENV=development / production（默认 development 兼容旧版）
_ENV = os.environ.get('FLASK_ENV', 'development').lower()
CONFIG_MAP = {
    'development': DevConfig,
    'dev': DevConfig,
    'production': ProdConfig,
    'prod': ProdConfig,
}
SelectedConfig = CONFIG_MAP.get(_ENV, DevConfig)
