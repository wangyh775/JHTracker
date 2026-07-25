"""集中配置：路径、密钥、分页大小等。"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'tracker.db')
RESUME_DIR = os.path.join(DATA_DIR, 'resumes')


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'local-dev-secret-key-2026')

    # career 数据源
    CAREER_DIR = os.environ.get('CAREER_DIR', 'D:/DJTU/HermesWorkspace/career')
    COMPANY_FILE_PATTERN = '企业清单_{source}_*.md'
    STUDY_FILE = '面试复习手册_自动化机电工程师.md'
    CODING_FILE = '面试编程题.md'

    # 分页
    PER_PAGE_COMPANIES = 40
    PER_PAGE_APPLICATIONS = 30
    PER_PAGE_NOTES = 30

    # 简历上传
    UPLOAD_FOLDER = RESUME_DIR
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB
    ALLOWED_RESUME_EXT = {'pdf', 'docx', 'doc'}
