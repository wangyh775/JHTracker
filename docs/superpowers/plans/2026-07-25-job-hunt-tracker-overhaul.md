# Job Hunt Tracker 全面改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 career-tracker 应用进行全面改造：修复 7 类既有问题、新增 5 项功能（备份/恢复、面试评价、Offer 对比、截止提醒、简历版本管理）、满足 5 项新需求（甘特图、LaTeX、公司薪资、看板 bug、前端微调），全程保留现有数据。

**Architecture:** Flask 应用工厂模式 + Blueprint 拆分。`app.py` 仅做工厂和启动；`config.py` / `constants.py` / `extensions.py` / `models.py` / `utils.py` 各司其职；`routes/` 目录按业务模块分文件。数据库走 Flask-Migrate（Alembic）做迁移，不删库。

**Tech Stack:** Flask 3.x + Flask-SQLAlchemy + Flask-Migrate + SQLite + Bootstrap 5 + Chart.js + chartjs-adapter-date-fns + KaTeX + mammoth.js + python-dateutil

**Spec:** [docs/superpowers/specs/2026-07-25-job-hunt-tracker-overhaul-design.md](file:///d:/DJTU/HermesWorkspace/career-tracker/docs/superpowers/specs/2026-07-25-job-hunt-tracker-overhaul-design.md)

**测试策略说明：** 本地单用户项目，纯工具函数（parse_date / validate_salary 等）写 pytest 单元测试；路由和前端走手动验证清单（每个任务末尾给出验证命令和预期结果）。

---

## 文件结构总览

**新建文件：**
- `config.py` — 配置集中
- `constants.py` — 业务常量
- `extensions.py` — db 实例
- `models.py` — 所有 ORM 模型
- `utils.py` — 工具函数
- `routes/__init__.py` — blueprint 聚合
- `routes/dashboard.py` / `company.py` / `application.py` / `note.py` / `study.py` / `timeline.py` / `import_data.py` / `backup.py` / `resume.py`
- `tests/test_utils.py` — 工具函数测试
- `tests/__init__.py`
- `templates/backup.html` / `compare.html` / `resumes.html` / `resume_preview.html` / `_feedback_form.html`

**修改文件：**
- `app.py` — 改为 app 工厂
- `templates/base.html` — 加 CSS 变量、移动端汉堡菜单、简历侧边栏入口
- `templates/dashboard.html` — 修图表 bug、加紧急横条、加面试复盘卡片
- `templates/companies.html` — 加薪资列、加总条数
- `templates/company_detail.html` — 加薪资显示、加面试评价区
- `templates/applications.html` — 加剩余天数列、加总条数
- `templates/study_content.html` — 引入 KaTeX
- `templates/timeline.html` — 改甘特图
- `templates/import.html` — 加简历导入提示（可选）
- `requirements.txt` — 加 Flask-Migrate

**删除文件：** 无（旧 `app.py` 被重写但保留同名）

---

## Task 1: 准备工作 — 依赖安装与数据库备份

**Files:**
- Modify: `requirements.txt`
- Create: `data/tracker.db.bak.<timestamp>`

- [ ] **Step 1: 备份现有数据库**

Run:
```bash
copy "data\tracker.db" "data\tracker.db.bak.20260725"
```

Expected: `data\tracker.db.bak.20260725` 文件存在且大小与原库一致。

- [ ] **Step 2: 更新 requirements.txt**

Modify `requirements.txt` to:

```
Flask>=3.0
Flask-SQLAlchemy>=3.1
Flask-Migrate>=4.0
python-dateutil>=2.8
```

- [ ] **Step 3: 安装新依赖**

Run:
```bash
pip install -r requirements.txt
```

Expected: `flask-migrate` 安装成功，`pip show flask-migrate` 输出版本号。

- [ ] **Step 4: 新建 data/resumes 目录**

Run:
```bash
mkdir data\resumes
```

- [ ] **Step 5: 提交**

```bash
git add requirements.txt data/
git commit -m "chore: add Flask-Migrate dep and backup db"
```

---

## Task 2: 创建 config.py — 配置集中化

**Files:**
- Create: `config.py`

- [ ] **Step 1: 写 config.py**

Create `config.py`:

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add config.py
git commit -m "feat: add config.py for centralized configuration"
```

---

## Task 3: 创建 constants.py — 业务常量

**Files:**
- Create: `constants.py`

- [ ] **Step 1: 写 constants.py**

Create `constants.py`:

```python
"""业务常量：状态、行业、城市、徽章颜色、优先级规则。"""

STATUS_LIST = ['待投递', '已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer', '已拒']

INDUSTRIES = ['3D打印', '机器人', '工业自动化', '高端装备', '汽车制造', '半导体设备',
              '能源与新能源', '医疗器械', '消费电子', '航空航天', '人工智能']

CITIES = ['深圳', '上海', '北京', '杭州', '广州', '武汉', '西安', '长沙', '南京', '成都']

STATUS_BADGE = {
    '待投递': 'secondary',
    '已投递': 'info',
    '简历筛选': 'primary',
    '笔试': 'warning',
    '一面': 'warning',
    '二面': 'warning',
    '终面': 'warning',
    'Offer': 'success',
    '已拒': 'danger',
}

# 优先级推断规则：名字包含关键字 → 优先级
PRIORITY_RULES = {
    'S': ['拓竹', 'INTAMSYS', '恒泰'],
    'A': ['创想', '纵维', '智能派', '汇川', '大疆'],
}

# 文件名 → 行业 映射
INDUSTRY_FROM_FILENAME = {
    '医疗': '医疗器械',
    '机器人': '机器人',
    '自动化': '工业自动化',
    '3D': '3D打印',
}

# Offer 状态
OFFER_STATUS_CHOICES = ['pending', 'accepted', 'rejected']
OFFER_STATUS_BADGE = {
    'pending': 'warning',
    'accepted': 'success',
    'rejected': 'secondary',
}
OFFER_STATUS_LABEL = {
    'pending': '待定',
    'accepted': '已接受',
    'rejected': '已拒绝',
}


def infer_priority(name):
    """根据公司名推断优先级，默认 B。"""
    for p, keywords in PRIORITY_RULES.items():
        if any(kw in name for kw in keywords):
            return p
    return 'B'


def infer_industry_from_filename(filename):
    """根据导入文件名推断行业。"""
    for key, ind in INDUSTRY_FROM_FILENAME.items():
        if key in filename:
            return ind
    return '未知'
```

- [ ] **Step 2: 提交**

```bash
git add constants.py
git commit -m "feat: add constants.py with business constants"
```

---

## Task 4: 创建 extensions.py — db 实例

**Files:**
- Create: `extensions.py`

- [ ] **Step 1: 写 extensions.py**

Create `extensions.py`:

```python
"""SQLAlchemy 实例，独立于 app，供 app 工厂初始化。"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

- [ ] **Step 2: 提交**

```bash
git add extensions.py
git commit -m "feat: add extensions.py with db instance"
```

---

## Task 5: 创建 utils.py — 工具函数与校验

**Files:**
- Create: `utils.py`
- Create: `tests/__init__.py`
- Create: `tests/test_utils.py`

- [ ] **Step 1: 写 tests/__init__.py（空文件）**

Create `tests/__init__.py` (empty).

- [ ] **Step 2: 写 utils.py**

Create `utils.py`:

```python
"""工具函数：日期解析、整数转换、薪资校验、markdown 表格解析。"""
from datetime import datetime


def parse_date(s):
    """解析 YYYY-MM-DD 字符串为 date 对象。空串返回 None，格式错误抛 ValueError。"""
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except ValueError as e:
        raise ValueError(f'日期格式错误: {s!r}，期望 YYYY-MM-DD') from e


def try_int(s, default=None):
    """安全转 int，失败返回 default。"""
    if not s:
        return default
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def validate_salary(min_v, max_v):
    """校验薪资范围。min > max 抛 ValueError。"""
    if min_v is not None and max_v is not None and min_v > max_v:
        raise ValueError(f'薪资下限 {min_v} 不能大于上限 {max_v}')
    return min_v, max_v


def validate_dates(apply_date, deadline):
    """校验日期：截止日期不能早于投递日期。"""
    if apply_date and deadline and deadline < apply_date:
        raise ValueError('截止日期不能早于投递日期')
    return apply_date, deadline


def parse_markdown_table(lines):
    """解析 markdown 表格，返回 (headers, rows)。
    每行是 dict: {header: value}。
    跳过分隔行 |---|---|。
    """
    headers = []
    rows = []
    in_table = False
    for line in lines:
        if '|' not in line:
            if in_table and headers:
                break
            continue
        parts = [p.strip() for p in line.split('|')]
        # 去掉首尾空元素（split 首尾会产生空串）
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]
        if not parts:
            continue
        # 检测分隔行 |---|---|
        if all(set(p) <= set('-: ') and '-' in p for p in parts):
            continue
        if not headers:
            headers = [p.replace('**', '').strip() for p in parts]
            in_table = True
        else:
            if len(parts) == len(headers):
                rows.append(dict(zip(headers, parts)))
    return headers, rows


def safe_filename(name, ext):
    """生成安全存储文件名：{timestamp}_{uuid}.{ext}，避免中文乱码和重名。"""
    import uuid
    return f"{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"


def humanize_size(num_bytes):
    """字节数转人类可读：1.2 MB。"""
    if num_bytes < 1024:
        return f'{num_bytes} B'
    elif num_bytes < 1024 * 1024:
        return f'{num_bytes / 1024:.1f} KB'
    else:
        return f'{num_bytes / (1024 * 1024):.1f} MB'
```

- [ ] **Step 3: 写 tests/test_utils.py**

Create `tests/test_utils.py`:

```python
"""utils.py 的单元测试。"""
import pytest
from datetime import date
from utils import parse_date, try_int, validate_salary, validate_dates, parse_markdown_table, safe_filename, humanize_size


class TestParseDate:
    def test_normal(self):
        assert parse_date('2026-07-25') == date(2026, 7, 25)

    def test_with_time(self):
        assert parse_date('2026-07-25T12:00:00') == date(2026, 7, 25)

    def test_empty(self):
        assert parse_date('') is None
        assert parse_date(None) is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_date('2026/07/25')
        with pytest.raises(ValueError):
            parse_date('not-a-date')


class TestTryInt:
    def test_normal(self):
        assert try_int('123') == 123

    def test_invalid(self):
        assert try_int('abc') is None
        assert try_int('abc', default=0) == 0

    def test_empty(self):
        assert try_int('') is None
        assert try_int(None) is None


class TestValidateSalary:
    def test_valid(self):
        assert validate_salary(10, 20) == (10, 20)

    def test_equal(self):
        assert validate_salary(15, 15) == (15, 15)

    def test_none(self):
        assert validate_salary(None, 20) == (None, 20)
        assert validate_salary(10, None) == (10, None)

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            validate_salary(30, 20)


class TestValidateDates:
    def test_valid(self):
        d1, d2 = date(2026, 7, 1), date(2026, 8, 1)
        assert validate_dates(d1, d2) == (d1, d2)

    def test_none(self):
        assert validate_dates(None, date(2026, 8, 1)) == (None, date(2026, 8, 1))

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            validate_dates(date(2026, 8, 1), date(2026, 7, 1))


class TestParseMarkdownTable:
    def test_basic(self):
        lines = [
            '| 排名 | 公司 | 城市 |',
            '|---|---|---|',
            '| 1 | 拓竹 | 深圳 |',
            '| 2 | 创想 | 深圳 |',
        ]
        headers, rows = parse_markdown_table(lines)
        assert headers == ['排名', '公司', '城市']
        assert len(rows) == 2
        assert rows[0]['公司'] == '拓竹'
        assert rows[1]['城市'] == '深圳'

    def test_bold_headers(self):
        lines = [
            '| **公司** | **城市** |',
            '|---|---|',
            '| 拓竹 | 深圳 |',
        ]
        headers, rows = parse_markdown_table(lines)
        assert headers == ['公司', '城市']

    def test_no_table(self):
        lines = ['some text', 'no table here']
        headers, rows = parse_markdown_table(lines)
        assert headers == []
        assert rows == []


class TestSafeFilename:
    def test_format(self):
        name = safe_filename('中文简历.pdf', 'pdf')
        assert name.endswith('.pdf')
        assert '_' in name

    def test_no_chinese_in_storage(self):
        name = safe_filename('中文简历.pdf', 'pdf')
        # 存储文件名不应包含中文
        assert all(ord(c) < 128 for c in name)


class TestHumanizeSize:
    def test_bytes(self):
        assert humanize_size(500) == '500 B'

    def test_kb(self):
        assert humanize_size(2048) == '2.0 KB'

    def test_mb(self):
        assert humanize_size(1024 * 1024 * 5) == '5.0 MB'
```

- [ ] **Step 4: 安装 pytest**

Run:
```bash
pip install pytest
```

- [ ] **Step 5: 运行测试验证全部通过**

Run:
```bash
pytest tests/test_utils.py -v
```

Expected: 全部测试通过（约 17 个测试）。

- [ ] **Step 6: 提交**

```bash
git add utils.py tests/
git commit -m "feat: add utils.py with validation and parsing functions + tests"
```

---

## Task 6: 创建 models.py — 数据模型

**Files:**
- Create: `models.py`

- [ ] **Step 1: 写 models.py**

Create `models.py`:

```python
"""ORM 模型定义。"""
from datetime import datetime
from extensions import db


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    industry = db.Column(db.String(100))
    city = db.Column(db.String(100))
    sub_city = db.Column(db.String(100))
    job_type = db.Column(db.String(100))
    match_reason = db.Column(db.Text)
    priority = db.Column(db.String(4), index=True)  # S/A/B/C
    website = db.Column(db.String(500))
    source_list = db.Column(db.String(100))
    salary_min = db.Column(db.Integer)  # 公司级参考薪资下限 k/月
    salary_max = db.Column(db.Integer)  # 公司级参考薪资上限 k/月
    created_at = db.Column(db.DateTime, default=datetime.now)

    applications = db.relationship('Application', backref='company', lazy='dynamic', cascade='all,delete-orphan')
    notes = db.relationship('Note', backref='company', lazy='dynamic', cascade='all,delete-orphan')


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    position = db.Column(db.String(200))
    channel = db.Column(db.String(50))
    status = db.Column(db.String(50), default='待投递')
    apply_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    salary_min = db.Column(db.Integer)  # 投递时具体薪资下限
    salary_max = db.Column(db.Integer)
    job_desc = db.Column(db.Text)
    url = db.Column(db.String(500))
    feedback = db.Column(db.Text)
    offer_status = db.Column(db.String(20))  # pending/accepted/rejected，仅 status=Offer 时有意义
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    feedbacks = db.relationship('InterviewFeedback', backref='application',
                                cascade='all,delete-orphan', lazy='dynamic')


class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    category = db.Column(db.String(50))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(100))
    source_file = db.Column(db.String(200))
    summary = db.Column(db.Text)
    is_learned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Timeline(db.Model):
    __tablename__ = 'timeline'
    id = db.Column(db.Integer, primary_key=True)
    event_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # 甘特图结束日期，NULL 时等于 event_date
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class InterviewFeedback(db.Model):
    __tablename__ = 'interview_feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    interviewer = db.Column(db.String(100))
    interview_date = db.Column(db.Date)
    round = db.Column(db.String(20))  # 一面/二面/终面
    difficulty = db.Column(db.Integer)  # 1-5
    self_rating = db.Column(db.Integer)  # 1-5
    questions = db.Column(db.Text)
    improvement = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(50))
    file_path = db.Column(db.String(500), nullable=False)  # 相对路径 data/resumes/xxx.pdf
    file_type = db.Column(db.String(10))  # pdf / docx
    file_size = db.Column(db.Integer)
    note = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
```

- [ ] **Step 2: 提交**

```bash
git add models.py
git commit -m "feat: add models.py with all ORM models"
```

---

## Task 7: 创建 routes 包骨架

**Files:**
- Create: `routes/__init__.py`
- Create: `routes/dashboard.py` / `company.py` / `application.py` / `note.py` / `study.py` / `timeline.py` / `import_data.py` / `backup.py` / `resume.py`

- [ ] **Step 1: 写 routes/__init__.py**

Create `routes/__init__.py`:

```python
"""Blueprint 聚合：所有路由 blueprint 在此导入，供 app 工厂注册。"""
from . import dashboard, company, application, note, study, timeline, import_data, backup, resume

ALL_BLUEPRINTS = [
    dashboard.bp,
    company.bp,
    application.bp,
    note.bp,
    study.bp,
    timeline.bp,
    import_data.bp,
    backup.bp,
    resume.bp,
]
```

- [ ] **Step 2: 写 routes/dashboard.py**

Create `routes/dashboard.py`:

```python
"""看板路由。"""
from flask import Blueprint, render_template
from sqlalchemy import func
from extensions import db
from models import Company, Application, Timeline
from constants import STATUS_LIST
from sqlalchemy.orm import joinedload

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def dashboard():
    total = Company.query.count()
    applied = Application.query.filter(
        Application.status.in_(['已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer'])
    ).count()
    interviews = Application.query.filter(
        Application.status.in_(['一面', '二面', '终面'])
    ).count()
    offers = Application.query.filter_by(status='Offer').count()
    rejected = Application.query.filter_by(status='已拒').count()

    # funnel：单次 group_by 查询
    status_counts = db.session.query(
        Application.status, func.count(Application.id)
    ).group_by(Application.status).all()
    funnel = {s: 0 for s in STATUS_LIST}
    for s, c in status_counts:
        funnel[s] = c

    # city distribution：过滤 NULL 和空串，按数量降序
    city_counts = db.session.query(
        func.coalesce(Company.city, '未知'), func.count(Company.id)
    ).filter(
        func.coalesce(Company.city, '') != ''
    ).group_by(Company.city).order_by(func.count(Company.id).desc()).all()

    # industry distribution
    ind_counts = db.session.query(
        func.coalesce(Company.industry, '未知'), func.count(Company.id)
    ).filter(
        func.coalesce(Company.industry, '') != ''
    ).group_by(Company.industry).order_by(func.count(Company.id).desc()).all()

    # priority breakdown
    pri_counts = db.session.query(
        func.coalesce(Company.priority, '无'), func.count(Company.id)
    ).group_by(Company.priority).all()

    # timeline upcoming
    upcoming = Timeline.query.filter(Timeline.done == False).order_by(Timeline.event_date).limit(5).all()

    # recent：用 joinedload 修 N+1
    recent = Application.query.options(
        joinedload(Application.company)
    ).order_by(Application.updated_at.desc()).limit(5).all()

    # 紧急截止：未来 7 天内 deadline
    from datetime import date, timedelta
    today = date.today()
    week_later = today + timedelta(days=7)
    urgent_deadlines = Application.query.filter(
        Application.deadline != None,
        Application.deadline >= today,
        Application.deadline <= week_later,
        ~Application.status.in_(['Offer', '已拒'])
    ).order_by(Application.deadline).all()

    # 面试复盘待写：status in (一面,二面,终面,Offer) 且无 feedbacks
    pending_feedbacks = Application.query.filter(
        Application.status.in_(['一面', '二面', '终面', 'Offer'])
    ).all()
    pending_feedbacks = [a for a in pending_feedbacks if a.feedbacks.count() == 0]

    max_funnel = max(funnel.values()) if funnel.values() else 1

    return render_template('dashboard.html',
                           total=total, applied=applied, interviews=interviews,
                           offers=offers, rejected=rejected,
                           funnel=funnel, max_funnel=max_funnel,
                           city_counts=city_counts, ind_counts=ind_counts,
                           pri_counts=pri_counts, upcoming=upcoming, recent=recent,
                           urgent_deadlines=urgent_deadlines,
                           pending_feedbacks=pending_feedbacks)
```

- [ ] **Step 3: 写 routes/company.py**

Create `routes/company.py`:

```python
"""公司清单路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Company
from constants import INDUSTRIES, CITIES
from utils import validate_salary

bp = Blueprint('company', __name__)


@bp.route('/companies')
def company_list():
    page = request.args.get('page', 1, type=int)
    ind = request.args.get('industry', '')
    ct = request.args.get('city', '')
    pr = request.args.get('priority', '')
    q = request.args.get('q', '')

    query = Company.query
    if ind:
        query = query.filter_by(industry=ind)
    if ct:
        query = query.filter(Company.city.contains(ct))
    if pr:
        query = query.filter_by(priority=pr)
    if q:
        query = query.filter(Company.name.contains(q) | Company.match_reason.contains(q))

    # NULL priority 排最后
    from sqlalchemy import desc
    query = query.order_by(Company.priority.is_(None), Company.priority, Company.name)
    companies = query.paginate(page=page, per_page=40)
    return render_template('companies.html', companies=companies,
                           industries=INDUSTRIES, cities=CITIES)


@bp.route('/companies/<int:c_id>')
def company_detail(c_id):
    c = Company.query.get_or_404(c_id)
    apps = c.applications.order_by(Application.updated_at.desc()).all() if False else c.applications.order_by(
        db.text('updated_at desc')).all()
    notes = c.notes.order_by(db.text('created_at desc')).all()
    return render_template('company_detail.html', company=c, apps=apps, notes=notes)


@bp.route('/companies/add', methods=['POST'])
def company_add():
    from utils import try_int
    try:
        salary_min = try_int(request.form.get('salary_min'))
        salary_max = try_int(request.form.get('salary_max'))
        validate_salary(salary_min, salary_max)
        c = Company(
            name=request.form['name'].strip(),
            industry=request.form.get('industry', '').strip(),
            city=request.form.get('city', '').strip(),
            sub_city=request.form.get('sub_city', '').strip(),
            job_type=request.form.get('job_type', '').strip(),
            match_reason=request.form.get('match_reason', '').strip(),
            priority=request.form.get('priority', 'B'),
            website=request.form.get('website', '').strip(),
            source_list=request.form.get('source_list', '').strip(),
            salary_min=salary_min,
            salary_max=salary_max,
        )
        db.session.add(c)
        db.session.commit()
    except ValueError as e:
        # 闪回错误信息（简化处理：直接 redirect）
        return redirect(url_for('company.company_list'))
    return redirect(url_for('company.company_list'))


@bp.route('/companies/<int:c_id>/edit', methods=['POST'])
def company_edit(c_id):
    from utils import try_int
    c = Company.query.get_or_404(c_id)
    try:
        salary_min = try_int(request.form.get('salary_min'))
        salary_max = try_int(request.form.get('salary_max'))
        validate_salary(salary_min, salary_max)
        c.name = request.form.get('name', c.name).strip()
        c.industry = request.form.get('industry', c.industry).strip()
        c.city = request.form.get('city', c.city).strip()
        c.sub_city = request.form.get('sub_city', c.sub_city).strip()
        c.job_type = request.form.get('job_type', c.job_type).strip()
        c.match_reason = request.form.get('match_reason', c.match_reason).strip()
        c.priority = request.form.get('priority', c.priority)
        c.website = request.form.get('website', c.website).strip()
        c.salary_min = salary_min
        c.salary_max = salary_max
        db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('company.company_detail', c_id=c_id))


@bp.route('/companies/<int:c_id>/delete', methods=['POST'])
def company_delete(c_id):
    c = Company.query.get_or_404(c_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('company.company_list'))


@bp.route('/api/companies/search')
def api_company_search():
    q = request.args.get('q', '')
    if not q:
        return []
    cs = Company.query.filter(Company.name.contains(q)).limit(10).all()
    return [{'id': c.id, 'name': c.name, 'city': c.city, 'industry': c.industry} for c in cs]
```

注意：company_detail 中用 `db.text` 是为了避免循环 import Application。实际可改为在顶部 import。

- [ ] **Step 4: 写 routes/application.py**

Create `routes/application.py`:

```python
"""投递记录路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy.orm import joinedload
from extensions import db
from models import Application, Company, InterviewFeedback
from constants import STATUS_LIST, OFFER_STATUS_CHOICES, OFFER_STATUS_LABEL, OFFER_STATUS_BADGE
from utils import parse_date, try_int, validate_salary, validate_dates

bp = Blueprint('application', __name__)


@bp.route('/applications')
def app_list():
    page = request.args.get('page', 1, type=int)
    st = request.args.get('status', '')
    ch = request.args.get('channel', '')
    query = Application.query.options(joinedload(Application.company))
    if st:
        query = query.filter_by(status=st)
    if ch:
        query = query.filter_by(channel=ch)
    apps = query.order_by(Application.updated_at.desc()).paginate(page=page, per_page=30)
    channels = db.session.query(
        Application.channel, db.func.count(Application.id)
    ).group_by(Application.channel).all()
    return render_template('applications.html', apps=apps, channels=channels,
                           status_list=STATUS_LIST)


@bp.route('/applications/add', methods=['POST'])
def app_add():
    try:
        salary_min = try_int(request.form.get('salary_min'))
        salary_max = try_int(request.form.get('salary_max'))
        validate_salary(salary_min, salary_max)
        apply_date = parse_date(request.form.get('apply_date', ''))
        deadline = parse_date(request.form.get('deadline', ''))
        validate_dates(apply_date, deadline)
        a = Application(
            company_id=request.form['company_id'],
            position=request.form.get('position', '').strip(),
            channel=request.form.get('channel', '').strip(),
            status=request.form.get('status', '待投递'),
            apply_date=apply_date,
            deadline=deadline,
            salary_min=salary_min,
            salary_max=salary_max,
            job_desc=request.form.get('job_desc', ''),
            url=request.form.get('url', '').strip(),
        )
        db.session.add(a)
        db.session.commit()
    except ValueError:
        pass
    return redirect(request.referrer or url_for('application.app_list'))


@bp.route('/applications/<int:a_id>/status', methods=['POST'])
def app_status(a_id):
    a = Application.query.get_or_404(a_id)
    a.status = request.form['status']
    if 'feedback' in request.form:
        a.feedback = request.form['feedback']
    db.session.commit()
    return redirect(request.referrer or url_for('application.app_list'))


@bp.route('/applications/<int:a_id>/offer_status', methods=['POST'])
def app_offer_status(a_id):
    a = Application.query.get_or_404(a_id)
    a.offer_status = request.form.get('offer_status', 'pending')
    db.session.commit()
    return redirect(request.referrer or url_for('application.compare'))


@bp.route('/applications/<int:a_id>/delete', methods=['POST'])
def app_delete(a_id):
    a = Application.query.get_or_404(a_id)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for('application.app_list'))


@bp.route('/applications/<int:a_id>/feedback/add', methods=['POST'])
def feedback_add(a_id):
    a = Application.query.get_or_404(a_id)
    f = InterviewFeedback(
        application_id=a.id,
        interviewer=request.form.get('interviewer', '').strip(),
        interview_date=parse_date(request.form.get('interview_date', '')),
        round=request.form.get('round', ''),
        difficulty=try_int(request.form.get('difficulty')),
        self_rating=try_int(request.form.get('self_rating')),
        questions=request.form.get('questions', ''),
        improvement=request.form.get('improvement', ''),
    )
    db.session.add(f)
    db.session.commit()
    return redirect(request.referrer or url_for('application.app_list'))


@bp.route('/applications/<int:a_id>/feedback/<int:f_id>/delete', methods=['POST'])
def feedback_delete(a_id, f_id):
    f = InterviewFeedback.query.get_or_404(f_id)
    db.session.delete(f)
    db.session.commit()
    return redirect(request.referrer or url_for('application.app_list'))


@bp.route('/compare')
def compare():
    offers = Application.query.options(joinedload(Application.company)).filter_by(
        status='Offer'
    ).order_by(Application.salary_max.desc().nullslast()).all()
    return render_template('compare.html', offers=offers,
                           offer_choices=OFFER_STATUS_CHOICES,
                           offer_labels=OFFER_STATUS_LABEL,
                           offer_badges=OFFER_STATUS_BADGE)
```

- [ ] **Step 5: 写 routes/note.py**

Create `routes/note.py`:

```python
"""笔记路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Note
from utils import try_int

bp = Blueprint('note', __name__)


@bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        n = Note(
            company_id=try_int(request.form.get('company_id')) or None,
            category=request.form.get('category', 'other'),
            title=request.form['title'],
            content=request.form.get('content', ''),
        )
        db.session.add(n)
        db.session.commit()
        return redirect(url_for('note.notes'))
    page = request.args.get('page', 1, type=int)
    ns = Note.query.order_by(Note.created_at.desc()).paginate(page=page, per_page=30)
    return render_template('notes.html', notes=ns)


@bp.route('/notes/<int:n_id>/delete', methods=['POST'])
def note_delete(n_id):
    n = Note.query.get_or_404(n_id)
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for('note.notes'))
```

- [ ] **Step 6: 写 routes/study.py**

Create `routes/study.py`:

```python
"""复习资料路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import StudyMaterial
from config import Config

bp = Blueprint('study', __name__)


@bp.route('/study')
def study_list():
    cat = request.args.get('category', '')
    query = StudyMaterial.query
    if cat:
        query = query.filter_by(category=cat)
    mats = query.order_by(StudyMaterial.category, StudyMaterial.title).all()
    return render_template('study.html', materials=mats)


@bp.route('/study/<int:m_id>/content')
def study_content(m_id):
    m = StudyMaterial.query.get_or_404(m_id)
    try:
        with open(m.source_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        content = f"无法读取文件 {m.source_file}: {str(e)}"
    return render_template('study_content.html', material=m, content=content)


@bp.route('/study/<int:m_id>/toggle', methods=['POST'])
def study_toggle(m_id):
    m = StudyMaterial.query.get_or_404(m_id)
    m.is_learned = not m.is_learned
    db.session.commit()
    return redirect(url_for('study.study_list'))
```

- [ ] **Step 7: 写 routes/timeline.py**

Create `routes/timeline.py`:

```python
"""时间线路由（甘特图）。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Timeline
from utils import parse_date

bp = Blueprint('timeline', __name__)


@bp.route('/timeline')
def timeline_view():
    items = Timeline.query.order_by(Timeline.event_date, Timeline.id).all()
    return render_template('timeline.html', items=items)


@bp.route('/timeline/add', methods=['POST'])
def timeline_add():
    try:
        event_date = parse_date(request.form['event_date'])
        end_date = parse_date(request.form.get('end_date', ''))
        if event_date is None:
            raise ValueError('开始日期不能为空')
        if end_date and end_date < event_date:
            raise ValueError('结束日期不能早于开始日期')
        t = Timeline(
            event_date=event_date,
            end_date=end_date,
            title=request.form['title'],
            description=request.form.get('description', ''),
            event_type=request.form.get('event_type', 'action'),
        )
        db.session.add(t)
        db.session.commit()
    except ValueError:
        pass
    return redirect(url_for('timeline.timeline_view'))


@bp.route('/timeline/<int:t_id>/toggle', methods=['POST'])
def timeline_toggle(t_id):
    t = Timeline.query.get_or_404(t_id)
    t.done = not t.done
    db.session.commit()
    return redirect(url_for('timeline.timeline_view'))
```

- [ ] **Step 8: 写 routes/import_data.py**

Create `routes/import_data.py`:

```python
"""数据导入路由：公司、复习资料、时间线。"""
import os
import glob
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Company, StudyMaterial, Timeline
from config import Config
from constants import infer_priority, infer_industry_from_filename
from utils import parse_markdown_table, parse_date

bp = Blueprint('import_data', __name__)


@bp.route('/import')
def import_page():
    return render_template('import.html')


@bp.route('/import/companies', methods=['POST'])
def import_companies():
    """从 career/ 目录的 markdown 清单批量导入公司。"""
    source = request.form.get('source', 'A')
    pattern = os.path.join(Config.CAREER_DIR, Config.COMPANY_FILE_PATTERN.format(source=source))
    files = glob.glob(pattern)
    if not files:
        all_md = glob.glob(os.path.join(Config.CAREER_DIR, '*.md'))
        files = [f for f in all_md if '企业清单' in os.path.basename(f)]

    imported_count = 0
    skipped_count = 0
    failed_rows = []

    for fp in files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            headers, rows = parse_markdown_table(lines)
            if not headers:
                failed_rows.append(f'{os.path.basename(fp)}: 未找到表格')
                continue

            # 找出列名对应的 header
            name_key = _find_header(headers, ['公司', '公司名称', '名称'])
            city_key = _find_header(headers, ['城市', '地点'])
            job_key = _find_header(headers, ['岗位', '职位', '方向'])
            reason_key = _find_header(headers, ['匹配', '理由', '匹配理由'])

            if not name_key:
                failed_rows.append(f'{os.path.basename(fp)}: 找不到公司名列')
                continue

            industry = infer_industry_from_filename(fp)

            for row in rows:
                name = row.get(name_key, '').replace('**', '').strip()
                if not name:
                    continue
                existing = Company.query.filter_by(name=name).first()
                if existing:
                    skipped_count += 1
                    continue
                priority = infer_priority(name)
                c = Company(
                    name=name,
                    industry=industry,
                    city=row.get(city_key, '').strip() if city_key else '',
                    job_type=row.get(job_key, '').strip() if job_key else '',
                    match_reason=row.get(reason_key, '').strip() if reason_key else '',
                    priority=priority,
                    source_list=f'清单{source}',
                )
                db.session.add(c)
                imported_count += 1
            db.session.commit()
        except Exception as e:
            failed_rows.append(f'{os.path.basename(fp)}: {str(e)}')

    if failed_rows:
        flash(f'导入完成。新增 {imported_count} 家，跳过 {skipped_count} 家。失败：{"; ".join(failed_rows)}')
    else:
        flash(f'导入完成。新增 {imported_count} 家，跳过 {skipped_count} 家。')
    return redirect(url_for('company.company_list'))


def _find_header(headers, candidates):
    """从 headers 中找第一个匹配 candidates 的列名。"""
    for h in headers:
        for c in candidates:
            if c in h:
                return h
    return None


@bp.route('/import/study', methods=['POST'])
def import_study():
    """从面试复习手册导入科目分类。"""
    path = os.path.join(Config.CAREER_DIR, Config.STUDY_FILE)
    cats = {
        '自动控制原理': 'control', '机械设计基础': 'mechanical', '传感器与检测技术': 'sensor',
        '电机与运动控制': 'motor', '嵌入式与编程': 'embedded', 'PLC与工业网络': 'plc',
        '热工基础': 'thermal', '面试行为问题': 'behavior'
    }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read()  # 仅验证可读
        for cn, cat in cats.items():
            existing = StudyMaterial.query.filter_by(category=cat).first()
            if not existing:
                sm = StudyMaterial(title=f"面试复习——{cn}", category=cat,
                                   source_file=path, summary=f"自动导入：{cn}", is_learned=False)
                db.session.add(sm)
        db.session.commit()
        flash('复习资料导入完成')
    except Exception as e:
        flash(f'复习资料导入失败：{str(e)}')

    path2 = os.path.join(Config.CAREER_DIR, Config.CODING_FILE)
    try:
        with open(path2, 'r', encoding='utf-8') as f:
            f.read()
        existing = StudyMaterial.query.filter_by(category='coding').first()
        if not existing:
            sm = StudyMaterial(title="面试编程题集（12题）", category='coding',
                               source_file=path2, summary="自动导入：PID仿真、串口通信、运动控制等", is_learned=False)
            db.session.add(sm)
            db.session.commit()
        flash('编程题集导入完成')
    except Exception as e:
        flash(f'编程题集导入失败：{str(e)}')

    return redirect(url_for('study.study_list'))


@bp.route('/import/timeline', methods=['POST'])
def import_timeline():
    """添加秋招关键节点。"""
    nodes = [
        ('2026-07-25', '2026-07-25', '秋招正式启动', '开始大规模投递，完成简历优化', 'action'),
        ('2026-08-15', '2026-08-15', '拓竹提前批截止', '确认投递状态', 'deadline'),
        ('2026-09-01', '2026-09-30', '秋招正式批高峰', '全面铺开投递，预计每日投3-5家', 'action'),
        ('2026-09-15', '2026-10-31', '面试高发期', '大量笔试/一面', 'milestone'),
        ('2026-10-01', '2026-10-31', '大论文初稿完成', '毕业论文主体完成，腾出精力面试', 'milestone'),
        ('2026-10-31', '2026-10-31', '秋招投递截止', '大部分公司秋招网申截止', 'deadline'),
        ('2026-11-01', '2026-11-15', 'Offer决策期', '评估所有offer，做最终决定', 'milestone'),
        ('2026-12-01', '2026-12-15', '毕业论文定稿', '修改完善论文准备答辩', 'deadline'),
        ('2027-03-01', '2027-04-30', '春招启动', '如秋招未果，春招补充', 'action'),
    ]
    added = 0
    for dt_start, dt_end, title, desc, typ in nodes:
        existing = Timeline.query.filter_by(title=title).first()
        if not existing:
            t = Timeline(
                event_date=parse_date(dt_start),
                end_date=parse_date(dt_end),
                title=title, description=desc, event_type=typ
            )
            db.session.add(t)
            added += 1
    db.session.commit()
    flash(f'时间线导入完成，新增 {added} 条')
    return redirect(url_for('timeline.timeline_view'))
```

- [ ] **Step 9: 写 routes/backup.py**

Create `routes/backup.py`:

```python
"""数据备份与恢复路由。"""
import os
import json
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from extensions import db
from models import Company, Application, Note, StudyMaterial, Timeline, InterviewFeedback, Resume

bp = Blueprint('backup', __name__)

BACKUP_VERSION = 1


@bp.route('/backup')
def backup_page():
    counts = {
        'companies': Company.query.count(),
        'applications': Application.query.count(),
        'notes': Note.query.count(),
        'study_materials': StudyMaterial.query.count(),
        'timelines': Timeline.query.count(),
        'interview_feedbacks': InterviewFeedback.query.count(),
        'resumes': Resume.query.count(),
    }
    return render_template('backup.html', counts=counts)


def _serialize(obj, model):
    """把 SQLAlchemy 对象序列化为 dict。"""
    result = {}
    for col in model.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        result[col.name] = val.isoformat() if hasattr(val, 'isoformat') and not isinstance(val, str) else val
    return result


@bp.route('/backup/export', methods=['POST'])
def backup_export():
    data = {
        'version': BACKUP_VERSION,
        'exported_at': datetime.now().isoformat(),
        'companies': [_serialize(c, Company) for c in Company.query.all()],
        'applications': [_serialize(a, Application) for a in Application.query.all()],
        'notes': [_serialize(n, Note) for n in Note.query.all()],
        'study_materials': [_serialize(s, StudyMaterial) for s in StudyMaterial.query.all()],
        'timelines': [_serialize(t, Timeline) for t in Timeline.query.all()],
        'interview_feedbacks': [_serialize(f, InterviewFeedback) for f in InterviewFeedback.query.all()],
        'resumes': [_serialize(r, Resume) for r in Resume.query.all()],
    }
    filename = f'tracker_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    backup_dir = os.path.join(current_app.config['BASE_DIR'] if hasattr(current_app.config, 'BASE_DIR') else os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    filepath = os.path.join(backup_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return send_file(filepath, as_attachment=True, download_name=filename)


@bp.route('/backup/restore', methods=['POST'])
def backup_restore():
    file = request.files.get('backup_file')
    if not file or not file.filename:
        flash('未选择文件')
        return redirect(url_for('backup.backup_page'))

    mode = request.form.get('mode', 'skip')  # skip / overwrite

    # 备份当前 db
    from config import Config
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    bak_path = f"{db_path}.before_restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, bak_path)

    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        if data.get('version') != BACKUP_VERSION:
            flash(f'版本不匹配：期望 {BACKUP_VERSION}，实际 {data.get("version")}')
            return redirect(url_for('backup.backup_page'))

        # 恢复顺序：companies → applications → notes → ...
        id_map = {'companies': {}}  # old_id -> new_id
        stats = {'companies': 0, 'applications': 0, 'notes': 0, 'timelines': 0,
                 'study_materials': 0, 'interview_feedbacks': 0, 'resumes': 0}

        for c_data in data.get('companies', []):
            name = c_data.get('name')
            existing = Company.query.filter_by(name=name).first()
            if existing and mode == 'skip':
                id_map['companies'][c_data['id']] = existing.id
                continue
            c_data.pop('id', None)
            c = Company(**{k: v for k, v in c_data.items() if v is not None or k in ['name']})
            db.session.add(c)
            db.session.flush()
            id_map['companies'][c_data.get('id', c.id)] = c.id
            stats['companies'] += 1

        for a_data in data.get('applications', []):
            old_company_id = a_data.get('company_id')
            a_data['company_id'] = id_map['companies'].get(old_company_id, old_company_id)
            a_data.pop('id', None)
            a = Application(**{k: v for k, v in a_data.items() if v is not None})
            db.session.add(a)
            stats['applications'] += 1

        for n_data in data.get('notes', []):
            old_company_id = n_data.get('company_id')
            if old_company_id:
                n_data['company_id'] = id_map['companies'].get(old_company_id, old_company_id)
            n_data.pop('id', None)
            db.session.add(Note(**{k: v for k, v in n_data.items() if v is not None}))

        for s_data in data.get('study_materials', []):
            s_data.pop('id', None)
            db.session.add(StudyMaterial(**{k: v for k, v in s_data.items() if v is not None}))

        for t_data in data.get('timelines', []):
            t_data.pop('id', None)
            db.session.add(Timeline(**{k: v for k, v in t_data.items() if v is not None}))

        db.session.commit()
        flash(f'恢复完成：{stats["companies"]} 家公司、{stats["applications"]} 条投递。当前 db 已备份到 {os.path.basename(bak_path)}')
    except Exception as e:
        db.session.rollback()
        flash(f'恢复失败：{str(e)}。当前 db 未变更（备份在 {os.path.basename(bak_path)}）')
    return redirect(url_for('backup.backup_page'))
```

- [ ] **Step 10: 写 routes/resume.py**

Create `routes/resume.py`:

```python
"""简历版本管理路由。"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models import Resume
from utils import safe_filename, humanize_size
from config import Config

bp = Blueprint('resume', __name__)


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_RESUME_EXT


@bp.route('/resumes')
def resume_list():
    resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    default_resume = Resume.query.filter_by(is_default=True).first()
    return render_template('resumes.html', resumes=resumes, default_resume=default_resume,
                           humanize_size=humanize_size)


@bp.route('/resumes/upload', methods=['POST'])
def resume_upload():
    file = request.files.get('file')
    if not file or not file.filename:
        flash('未选择文件')
        return redirect(url_for('resume.resume_list'))
    if not _allowed_file(file.filename):
        flash(f'不支持的文件类型，仅接受 {", ".join(Config.ALLOWED_RESUME_EXT)}')
        return redirect(url_for('resume.resume_list'))

    ext = file.filename.rsplit('.', 1)[1].lower()
    storage_name = safe_filename(file.filename, ext)
    storage_path = os.path.join(Config.UPLOAD_FOLDER, storage_name)
    file.save(storage_path)
    file_size = os.path.getsize(storage_path)

    # 如果是第一个简历，自动设为默认
    is_first = Resume.query.count() == 0

    r = Resume(
        name=request.form.get('name', file.filename).strip(),
        version=request.form.get('version', '').strip(),
        file_path=f'data/resumes/{storage_name}',
        file_type=ext,
        file_size=file_size,
        note=request.form.get('note', '').strip(),
        is_default=is_first,
    )
    db.session.add(r)
    db.session.commit()
    flash(f'上传成功：{r.name}')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/preview')
def resume_preview(r_id):
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.join(current_app.config['BASE_DIR'], r.file_path) if current_app.config.get('BASE_DIR') else os.path.abspath(r.file_path)
    return render_template('resume_preview.html', resume=r)


@bp.route('/resumes/<int:r_id>/file')
def resume_file(r_id):
    """返回原文件，供 iframe 或 fetch 使用。"""
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.abspath(r.file_path)
    return send_file(abs_path)


@bp.route('/resumes/<int:r_id>/download')
def resume_download(r_id):
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.abspath(r.file_path)
    return send_file(abs_path, as_attachment=True, download_name=f'{r.name}.{r.file_type}')


@bp.route('/resumes/<int:r_id>/edit', methods=['POST'])
def resume_edit(r_id):
    r = Resume.query.get_or_404(r_id)
    r.name = request.form.get('name', r.name).strip()
    r.version = request.form.get('version', r.version).strip()
    r.note = request.form.get('note', r.note).strip()
    db.session.commit()
    flash('已更新')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/default', methods=['POST'])
def resume_set_default(r_id):
    r = Resume.query.get_or_404(r_id)
    # 取消其他默认
    Resume.query.filter_by(is_default=True).update({'is_default': False})
    r.is_default = True
    db.session.commit()
    flash(f'已将「{r.name}」设为默认')
    return redirect(url_for('resume.resume_list'))


@bp.route('/resumes/<int:r_id>/delete', methods=['POST'])
def resume_delete(r_id):
    r = Resume.query.get_or_404(r_id)
    abs_path = os.path.abspath(r.file_path)
    try:
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except OSError:
        pass
    db.session.delete(r)
    db.session.commit()
    flash('已删除')
    return redirect(url_for('resume.resume_list'))
```

- [ ] **Step 11: 提交**

```bash
git add routes/
git commit -m "feat: add routes package with all blueprints"
```

---

## Task 8: 重写 app.py — 应用工厂

**Files:**
- Modify: `app.py`（完全重写）

- [ ] **Step 1: 重写 app.py**

Overwrite `app.py` with:

```python
"""Job Hunt Tracker — 应用工厂与启动入口。"""
import os
from flask import Flask
from config import Config
from extensions import db
from constants import STATUS_LIST, INDUSTRIES, CITIES, STATUS_BADGE
from datetime import datetime
from flask import g


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # 把 BASE_DIR 也塞进 config，方便 routes 用
    app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))

    db.init_app(app)

    # 注册所有 blueprint
    from routes import ALL_BLUEPRINTS
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # 上下文处理器：注入全局变量到模板
    @app.context_processor
    def inject_globals():
        return dict(
            status_list=STATUS_LIST,
            industries=INDUSTRIES,
            cities=CITIES,
            status_badge=STATUS_BADGE,
            now=datetime.now,
        )

    return app


app = create_app()


if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data', 'resumes'), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)
```

- [ ] **Step 2: 删除旧 app.py 中残留的旧逻辑（已被重写覆盖）**

确认 `app.py` 不再包含旧的 `Company` / `Application` 等模型定义和路由。

- [ ] **Step 3: 提交**

```bash
git add app.py
git commit -m "refactor: rewrite app.py as app factory with blueprints"
```

---

## Task 9: 初始化 Flask-Migrate

**Files:**
- Create: `migrations/`（自动生成）

- [ ] **Step 1: 设置 FLASK_APP 环境变量**

PowerShell:
```bash
$env:FLASK_APP = "app.py"
```

- [ ] **Step 2: 初始化 migrations 目录**

Run:
```bash
flask db init
```

Expected: 创建 `migrations/` 目录，包含 `alembic.ini`、`env.py`、`script.py.mako`、`versions/`。

- [ ] **Step 3: 标记当前数据库为基线**

Run:
```bash
flask db stamp head
```

Expected: 无报错。当前数据库被标记为 head（还没有迁移脚本）。

- [ ] **Step 4: 提交 migrations 骨架**

```bash
git add migrations/
git commit -m "chore: init Flask-Migrate"
```

---

## Task 10: 生成并执行第一次迁移

**Files:**
- Create: `migrations/versions/xxx_*.py`（自动生成）

- [ ] **Step 1: 生成迁移脚本**

Run:
```bash
flask db migrate -m "add company salary, application offer_status, interview_feedback, timeline end_date, resume"
```

Expected: 在 `migrations/versions/` 下生成新文件，包含：
- companies 表加 `salary_min` / `salary_max` 列
- applications 表加 `offer_status` 列
- timeline 表加 `end_date` 列
- 新建 `interview_feedbacks` 表
- 新建 `resumes` 表
- companies 表 `name` 加 unique 约束

- [ ] **Step 2: 人工审阅迁移脚本**

打开生成的迁移文件，检查：
- `upgrade()` 函数包含上述变更
- `downgrade()` 函数能回滚
- 没有意外的 drop_table

**注意：** 如果迁移脚本试图 `drop_table` + `create_table`（因为 unique 约束），需要手工改为 `batch_alter_table` 形式，避免数据丢失。SQLite 不支持直接加 unique 约束，需用 batch mode。

参考修改（如果脚本错误地重建 companies 表）：
```python
with op.batch_alter_table('companies') as batch_op:
    batch_op.alter_column('name', 'name', unique=True)
    batch_op.add_column(sa.Column('salary_min', sa.Integer(), nullable=True))
    batch_op.add_column(sa.Column('salary_max', sa.Integer(), nullable=True))
```

- [ ] **Step 3: 执行迁移**

Run:
```bash
flask db upgrade
```

Expected: 无报错。数据库 schema 更新。

- [ ] **Step 4: 验证数据未丢**

Run（PowerShell）:
```bash
python -c "from app import app; from app import app; from extensions import db; app.app_context().push(); from models import Company, Application; print(f'companies={Company.query.count()}, applications={Application.query.count()}')"
```

Expected: 公司数和投递数与迁移前一致。

- [ ] **Step 5: 提交**

```bash
git add migrations/versions/
git commit -m "db: migrate to add salary, offer_status, feedbacks, end_date, resumes"
```

---

## Task 11: 更新 base.html — CSS 变量、移动端汉堡菜单、简历入口

**Files:**
- Modify: `templates/base.html`

- [ ] **Step 1: 重写 base.html 的 <style> 块**

Replace the `<style>...</style>` block in `templates/base.html` with:

```html
<style>
:root {
  --bg-primary: #111;
  --bg-card: #1a1a1a;
  --bg-card-hover: #1f1f1f;
  --border: #2a2a2a;
  --text-primary: #e0e0e0;
  --text-secondary: #aaa;
  --accent: #0d6efd;
  --shadow: 0 2px 8px rgba(0,0,0,0.15);
  --shadow-hover: 0 4px 16px rgba(0,0,0,0.25);
  --radius: 12px;
  --transition: all 0.15s ease;
}
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 14px;
}
.sidebar {
  background: var(--bg-card);
  min-height: 100vh;
  border-right: 1px solid var(--border);
}
.sidebar .nav-link {
  color: var(--text-secondary);
  padding: 0.6rem 1rem;
  border-radius: 6px;
  margin: 2px 0;
  transition: var(--transition);
  position: relative;
}
.sidebar .nav-link:hover {
  color: #fff;
  background: #2a2a2a;
}
.sidebar .nav-link.active {
  color: #fff;
  background: var(--accent);
}
.sidebar .nav-link.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: #fff;
  border-radius: 2px;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--shadow);
  transition: var(--transition);
}
.stat-card:hover { box-shadow: var(--shadow-hover); }
.stat-card .num { font-size: 2rem; font-weight: 700; }
.badge-priority-S { background: #dc3545; }
.badge-priority-A { background: #fd7e14; }
.badge-priority-B { background: #0d6efd; }
.badge-priority-C { background: #6c757d; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.funnel-bar { height: 24px; border-radius: 4px; margin: 2px 0; transition: width 0.3s; }
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  transition: var(--transition);
}
.card:hover { box-shadow: var(--shadow-hover); }
.modal-content { background: var(--bg-card); border: 1px solid #333; }
.table { color: var(--text-primary); }
.table-hover tbody tr {
  transition: var(--transition);
  position: relative;
}
.table-hover tbody tr:hover {
  color: #fff;
  background: var(--bg-card-hover);
  box-shadow: inset 3px 0 0 var(--accent);
}
.form-control, .form-select {
  background: #222;
  border: 1px solid #333;
  color: var(--text-primary);
  transition: var(--transition);
}
.form-control:focus, .form-select:focus {
  background: #222;
  color: #fff;
  border-color: var(--accent);
  box-shadow: 0 0 0 0.2rem rgba(13,110,253,0.25);
}
.btn { transition: var(--transition); }
.btn-outline-light:hover { color: #000; }
.badge { border-radius: 6px; padding: 0.4em 0.7em; }
a { color: #6ea8fe; transition: var(--transition); }
a:hover { color: #8ab4ff; }
.dashboard-title { font-size: 1.5rem; font-weight: 600; }
.funnel-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.funnel-label { width: 80px; text-align: right; font-size: 0.85rem; flex-shrink: 0; }
.funnel-bar-wrap { flex: 1; background: #222; border-radius: 4px; overflow: hidden; }
.funnel-bar-fill { height: 22px; border-radius: 4px; }
.funnel-count { width: 40px; text-align: right; font-size: 0.85rem; flex-shrink: 0; }
.bi { font-size: 14px; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #444; }
.urgent-banner {
  background: linear-gradient(90deg, rgba(220,53,69,0.15), rgba(255,193,7,0.15));
  border: 1px solid rgba(220,53,69,0.3);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}
</style>
```

- [ ] **Step 2: 在 <head> 加入 Inter 字体**

在 `templates/base.html` 的 `<head>` 内（在 bootstrap CSS 之后）加：

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

- [ ] **Step 3: 改 sidebar 为可折叠 + 加简历入口**

Replace the sidebar block（`<div class="col-md-2 sidebar p-3 d-none d-md-block">...</div>`）with:

```html
<!-- Mobile topbar -->
<nav class="navbar navbar-dark bg-dark d-md-none">
  <div class="container-fluid">
    <button class="navbar-toggler" type="button" data-bs-toggle="offcanvas" data-bs-target="#sidebarOffcanvas">
      <span class="navbar-toggler-icon"></span>
    </button>
    <span class="navbar-brand"><i class="bi bi-rocket-takeoff me-1"></i>JHTracker</span>
  </div>
</nav>

<!-- Sidebar (desktop) -->
<div class="col-md-2 sidebar p-3 d-none d-md-block">
  {% include '_sidebar.html' %}
</div>

<!-- Sidebar (mobile offcanvas) -->
<div class="offcanvas offcanvas-start bg-dark text-white" tabindex="-1" id="sidebarOffcanvas">
  <div class="offcanvas-body">
    {% include '_sidebar.html' %}
  </div>
</div>
```

- [ ] **Step 4: 创建 _sidebar.html 局部模板**

Create `templates/_sidebar.html`:

```html
<div class="d-flex align-items-center mb-4 mt-2">
  <i class="bi bi-rocket-takeoff fs-3 me-2 text-primary"></i>
  <span class="fw-bold fs-5">JHTracker</span>
</div>
<hr class="text-secondary">
<nav class="nav flex-column">
  <a class="nav-link {% if request.path=='/' %}active{% endif %}" href="/"><i class="bi bi-speedometer2 me-2"></i>看板</a>
  <a class="nav-link {% if 'companies' in request.path %}active{% endif %}" href="/companies"><i class="bi bi-building me-2"></i>公司清单</a>
  <a class="nav-link {% if 'applications' in request.path %}active{% endif %}" href="/applications"><i class="bi bi-send me-2"></i>投递记录</a>
  <a class="nav-link {% if 'notes' in request.path %}active{% endif %}" href="/notes"><i class="bi bi-journal-text me-2"></i>笔记</a>
  <a class="nav-link {% if 'study' in request.path %}active{% endif %}" href="/study"><i class="bi bi-book me-2"></i>复习资料</a>
  <a class="nav-link {% if 'timeline' in request.path %}active{% endif %}" href="/timeline"><i class="bi bi-calendar3 me-2"></i>时间线</a>
  <a class="nav-link {% if 'resumes' in request.path %}active{% endif %}" href="/resumes"><i class="bi bi-file-earmark-person me-2"></i>简历版本</a>
  <a class="nav-link {% if 'compare' in request.path %}active{% endif %}" href="/compare"><i class="bi bi-trophy me-2"></i>Offer 对比</a>
  <a class="nav-link {% if 'backup' in request.path %}active{% endif %}" href="/backup"><i class="bi bi-shield-lock me-2"></i>备份/恢复</a>
  <a class="nav-link {% if 'import' in request.path %}active{% endif %}" href="/import"><i class="bi bi-upload me-2"></i>数据导入</a>
</nav>
<hr class="text-secondary">
<div class="text-secondary small px-2">
  <i class="bi bi-person-circle me-1"></i> 老大<br>
  <span class="small">自动化/机电工程师</span>
</div>
```

- [ ] **Step 5: 提交**

```bash
git add templates/base.html templates/_sidebar.html
git commit -m "feat: add CSS variables, mobile sidebar, resume nav entry"
```

---

## Task 12: 修复 dashboard.html — 图表 bug + 紧急横条 + 面试复盘卡片

**Files:**
- Modify: `templates/dashboard.html`

- [ ] **Step 1: 在 stats row 上方加紧急截止横条**

在 `{% block content %}` 之后、stats row 之前插入：

```html
{% if urgent_deadlines %}
<div class="urgent-banner">
  <div class="d-flex align-items-center">
    <i class="bi bi-alarm-fill text-danger me-2 fs-5"></i>
    <strong class="me-3">本周紧急截止：</strong>
    <div class="d-flex flex-wrap gap-3">
      {% for a in urgent_deadlines[:5] %}
      <span class="small">
        <a href="/companies/{{ a.company_id }}" class="text-decoration-none">
          {{ a.company.name }}
        </a>
        <span class="badge bg-danger ms-1">{{ a.deadline.strftime('%m/%d') }}</span>
      </span>
      {% endfor %}
    </div>
  </div>
</div>
{% endif %}
```

- [ ] **Step 2: 在最近动态卡片下方加面试复盘待写卡片**

在 "最近动态" 那个 `<div class="col-md-4">` 之后（即第三行 row 内）追加一个 col，或新起一行。最简单：把 `recent` 卡片所在 row 改为 4 列（看板顶部的 priority/upcoming/recent 行），或在最下方加一行：

在最后一个 `</div>` （关闭 `<div class="row g-3">`）之后加：

```html
{% if pending_feedbacks %}
<div class="row g-3 mt-1">
  <div class="col-12">
    <div class="card border-warning">
      <div class="card-body">
        <h6 class="card-title mb-3"><i class="bi bi-clipboard-check me-2 text-warning"></i>面试复盘待写</h6>
        <div class="d-flex flex-wrap gap-2">
          {% for a in pending_feedbacks %}
          <a href="/companies/{{ a.company_id }}" class="badge bg-warning text-dark text-decoration-none">
            {{ a.company.name }} — {{ a.status }}
          </a>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>
</div>
{% endif %}
```

- [ ] **Step 3: 修复图表 backgroundColor 数组**

在 `{% block scripts %}` 内，把 cityChart 的 `backgroundColor` 改为：

```javascript
const palette = ['#0d6efd','#6f42c1','#fd7e14','#20c997','#dc3545','#ffc107','#198754','#0dcaf0','#d63384','#adb5bd','#6610f2','#0dcaf0','#fd7e14','#20c997','#6c757d'];
```

cityChart dataset 改为：
```javascript
backgroundColor: [{% for c,n in city_counts %}palette[{{ loop.index0 }} % palette.length]{% if not loop.last %},{% endif %}{% endfor %}]
```

industryChart dataset 同理：
```javascript
backgroundColor: [{% for c,n in ind_counts %}palette[{{ loop.index0 }} % palette.length]{% if not loop.last %},{% endif %}{% endfor %}]
```

- [ ] **Step 4: 提交**

```bash
git add templates/dashboard.html
git commit -m "fix: dashboard chart colors, add urgent banner and feedback reminders"
```

---

## Task 13: 更新 companies.html — 加薪资列 + 总条数

**Files:**
- Modify: `templates/companies.html`

- [ ] **Step 1: 表头加"参考薪资"列**

把表头那行改为：

```html
<tr><th>优先级</th><th>公司名称</th><th>行业</th><th>城市</th><th>岗位方向</th><th>参考薪资</th><th>匹配理由</th><th></th></tr>
```

- [ ] **Step 2: 表体加薪资单元格**

在 `<td class="small">{{ c.job_type or '-' }}</td>` 之后、`<td class="small text-secondary" ...>{{ c.match_reason or '-' }}</td>` 之前插入：

```html
<td class="small">
  {% if c.salary_min or c.salary_max %}
  {{ c.salary_min or '?' }}-{{ c.salary_max or '?' }}k
  {% else %}-{% endif %}
</td>
```

- [ ] **Step 3: 空状态 colspan 改为 8**

把 `{% else %}` 分支的 `<td colspan="7"` 改为 `<td colspan="8"`。

- [ ] **Step 4: 在标题旁加总条数显示**

标题行已有 `<span class="badge bg-primary fs-6">{{ companies.total }}</span>`，保留。

- [ ] **Step 5: 在添加公司 modal 加薪资输入**

在 modal-body 的 `<div class="row g-3">` 内，"岗位方向" 那个 col 之后加：

```html
<div class="col-md-3"><label class="form-label">参考薪资下限 (k)</label><input type="number" class="form-control" name="salary_min" min="0"></div>
<div class="col-md-3"><label class="form-label">参考薪资上限 (k)</label><input type="number" class="form-control" name="salary_max" min="0"></div>
```

（调整其他 col 的 col-md-X 使布局合理，比如岗位方向从 col-md-6 改 col-md-6 → col-md-3，来源清单保持 col-md-6 或调整）

- [ ] **Step 6: 提交**

```bash
git add templates/companies.html
git commit -m "feat: add salary column to company list"
```

---

## Task 14: 更新 company_detail.html — 薪资显示 + 面试评价区

**Files:**
- Modify: `templates/company_detail.html`
- Create: `templates/_feedback_form.html`

- [ ] **Step 1: 先读取现有 company_detail.html 了解结构**

Run: 用 Read 工具读 `templates/company_detail.html` 全文。

- [ ] **Step 2: 在公司信息块加参考薪资**

在公司信息展示区（通常是一个 card 或 info 块）加：

```html
<div class="mb-2">
  <span class="text-secondary small">参考薪资：</span>
  {% if company.salary_min or company.salary_max %}
  <strong>{{ company.salary_min or '?' }}-{{ company.salary_max or '?' }}k/月</strong>
  {% else %}<span class="text-secondary">未填写</span>{% endif %}
</div>
```

- [ ] **Step 3: 创建 _feedback_form.html**

Create `templates/_feedback_form.html`:

```html
<!-- 面试评价表单（局部模板，传 application 对象 a） -->
<div class="card mt-3">
  <div class="card-body">
    <h6 class="card-title"><i class="bi bi-chat-quote me-2"></i>添加面试评价</h6>
    <form method="post" action="/applications/{{ a.id }}/feedback/add">
      <div class="row g-2">
        <div class="col-md-4"><label class="form-label small">面试官</label><input class="form-control form-control-sm" name="interviewer"></div>
        <div class="col-md-3"><label class="form-label small">面试日期</label><input type="date" class="form-control form-control-sm" name="interview_date"></div>
        <div class="col-md-2"><label class="form-label small">轮次</label>
          <select class="form-select form-select-sm" name="round">
            <option value="一面">一面</option>
            <option value="二面">二面</option>
            <option value="终面">终面</option>
            <option value="HR面">HR面</option>
          </select>
        </div>
        <div class="col-md-1"><label class="form-label small">难度</label><input type="number" class="form-control form-control-sm" name="difficulty" min="1" max="5"></div>
        <div class="col-md-2"><label class="form-label small">自评</label><input type="number" class="form-control form-control-sm" name="self_rating" min="1" max="5"></div>
        <div class="col-12"><label class="form-label small">问题记录</label><textarea class="form-control form-control-sm" name="questions" rows="2"></textarea></div>
        <div class="col-12"><label class="form-label small">改进点</label><textarea class="form-control form-control-sm" name="improvement" rows="2"></textarea></div>
        <div class="col-12"><button class="btn btn-sm btn-primary">保存评价</button></div>
      </div>
    </form>

    {% for f in a.feedbacks.all() %}
    <div class="border-top mt-2 pt-2">
      <div class="d-flex justify-content-between">
        <strong>{{ f.round }} · {{ f.interviewer or '未知面试官' }}</strong>
        <span class="text-secondary small">{{ f.interview_date.strftime('%Y-%m-%d') if f.interview_date else '' }}</span>
      </div>
      <div class="small text-secondary">
        难度 {{ f.difficulty or '-' }}/5 · 自评 {{ f.self_rating or '-' }}/5
      </div>
      {% if f.questions %}<div class="small mt-1"><strong>问题：</strong>{{ f.questions }}</div>{% endif %}
      {% if f.improvement %}<div class="small"><strong>改进：</strong>{{ f.improvement }}</div>{% endif %}
      <form method="post" action="/applications/{{ a.id }}/feedback/{{ f.id }}/delete" class="d-inline">
        <button class="btn btn-sm btn-link text-danger p-0">删除</button>
      </form>
    </div>
    {% endfor %}
  </div>
</div>
```

- [ ] **Step 4: 在投递记录循环里 include 评价表单**

在 company_detail.html 中，每条 application 的展示区块之后 include：

```html
{% for a in apps %}
<div class="card mb-3">
  <div class="card-body">
    <!-- 现有投递信息展示 -->
    ...
    {% include '_feedback_form.html' with context %}
  </div>
</div>
{% endfor %}
```

注意：因为 `_feedback_form.html` 用了变量 `a`，需要确保 include 时 `a` 在作用域内。Jinja2 的 `with context` 会传递当前上下文，`a` 已经在循环里。

- [ ] **Step 5: 提交**

```bash
git add templates/company_detail.html templates/_feedback_form.html
git commit -m "feat: add salary display and interview feedback in company detail"
```

---

## Task 15: 更新 applications.html — 剩余天数列 + 总条数

**Files:**
- Modify: `templates/applications.html`

- [ ] **Step 1: 先读取现有 applications.html**

Run: 用 Read 工具读全文。

- [ ] **Step 2: 表头加"剩余天数"列**

在表头加一列（在状态列之后或截止日期列之后）：

```html
<th>剩余天数</th>
```

- [ ] **Step 3: 表体加剩余天数单元格**

在对应行加：

```html
<td class="small">
  {% if a.deadline %}
    {% set days_left = (a.deadline - now().date()).days %}
    {% if days_left < 0 %}
    <span class="text-danger">已过期 {{ -days_left }} 天</span>
    {% elif days_left <= 3 %}
    <span class="text-warning">剩 {{ days_left }} 天</span>
    {% elif days_left <= 7 %}
    <span class="text-warning">剩 {{ days_left }} 天</span>
    {% else %}
    <span class="text-secondary">剩 {{ days_left }} 天</span>
    {% endif %}
  {% else %}-{% endif %}
</td>
```

- [ ] **Step 4: 标题旁加总条数**

在标题行加 `<span class="badge bg-primary">{{ apps.total }}</span>`。

- [ ] **Step 5: 空状态 colspan 调整**

如果加了列，colspan 加 1。

- [ ] **Step 6: 提交**

```bash
git add templates/applications.html
git commit -m "feat: add days-left column and total count to applications"
```

---

## Task 16: 更新 study_content.html — KaTeX 渲染

**Files:**
- Modify: `templates/study_content.html`

- [ ] **Step 1: 在 <head> 区引入 KaTeX**

在 base.html 的 `{% block scripts %}` 之前，study_content.html 内加一个 `{% block head %}`（需要先在 base.html 留好这个 block）。

更简单：直接在 study_content.html 的 content block 顶部加：

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" defer></script>
```

- [ ] **Step 2: 改写 <script> 块，加 KaTeX 渲染**

把现有 script 块改为：

```html
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
<script>
const rawContent = {{ content | tojson }};
const elem = document.getElementById('content');

// 预处理：把 $...$ 和 $$...$$ 内的内容用占位符保护，避免 marked.js 破坏 LaTeX
const placeholders = [];
function protectMath(text) {
  return text.replace(/\$\$([\s\S]+?)\$\$/g, (m, p1) => {
    placeholders.push({display: true, content: p1});
    return `MATHPLACEHOLDER${placeholders.length - 1}END`;
  }).replace(/\$([^\n$]+?)\$/g, (m, p1) => {
    placeholders.push({display: false, content: p1});
    return `MATHPLACEHOLDER${placeholders.length - 1}END`;
  });
}
function restoreMath(html) {
  return html.replace(/MATHPLACEHOLDER(\d+)END/g, (m, idx) => {
    const item = placeholders[parseInt(idx)];
    return item.display ? `$$${item.content}$$` : `$${item.content}$`;
  });
}

const protected = protectMath(rawContent);
let html;
{% if '面试复习手册' in material.source_file %}
const sections = {
  'control': '自动控制原理', 'mechanical': '机械设计基础', 'sensor': '传感器与检测技术',
  'motor': '电机与运动控制', 'embedded': '嵌入式与编程', 'plc': 'PLC与工业网络',
  'thermal': '热工基础', 'behavior': '面试行为问题'
};
const sectionTitle = sections['{{ material.category }}'];
const idx = rawContent.indexOf('## ' + sectionTitle);
if (idx > 0) {
  html = marked.parse(protectMath(rawContent.substring(idx)));
} else {
  html = marked.parse(protected);
}
{% else %}
html = marked.parse(protected);
{% endif %}
elem.innerHTML = restoreMath(html);

// KaTeX 渲染
if (window.renderMathInElement) {
  renderMathInElement(elem, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false},
      {left: '\\(', right: '\\)', display: false},
      {left: '\\[', right: '\\]', display: true}
    ],
    throwOnError: false
  });
} else {
  document.addEventListener('DOMContentLoaded', () => {
    renderMathInElement(elem, {
      delimiters: [
        {left: '$$', right: '$$', display: true},
        {left: '$', right: '$', display: false},
        {left: '\\(', right: '\\)', display: false},
        {left: '\\[', right: '\\]', display: true}
      ],
      throwOnError: false
    });
  });
}
</script>
```

- [ ] **Step 3: 提交**

```bash
git add templates/study_content.html
git commit -m "feat: add KaTeX rendering for LaTeX formulas"
```

---

## Task 17: 重写 timeline.html — 甘特图

**Files:**
- Modify: `templates/timeline.html`

- [ ] **Step 1: 完全重写 timeline.html**

Overwrite `templates/timeline.html` with:

```html
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <div class="dashboard-title"><i class="bi bi-calendar3 me-2 text-primary"></i>时间线（甘特图）</div>
  <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addModal"><i class="bi bi-plus-lg me-1"></i>添加节点</button>
</div>

<!-- 甘特图 -->
<div class="card mb-4">
  <div class="card-body">
    <h6 class="card-title mb-3"><i class="bi bi-bar-chart-steps me-2"></i>时间甘特图</h6>
    <div style="height: 400px;">
      <canvas id="ganttChart"></canvas>
    </div>
  </div>
</div>

<!-- 列表详情 -->
<div class="card">
  <div class="card-body">
    <h6 class="card-title mb-3"><i class="bi bi-list-ul me-2"></i>节点详情</h6>
    {% for item in items %}
    <div id="item-{{ item.id }}" class="border-bottom py-2 {% if item.done %}opacity-50{% endif %}">
      <div class="d-flex align-items-center">
        <span class="badge {% if item.event_type=='deadline' %}bg-danger{% elif item.event_type=='milestone' %}bg-warning text-dark{% elif item.event_type=='reminder' %}bg-secondary{% else %}bg-primary{% endif %} me-2">
          {{ item.event_type }}
        </span>
        <strong class="me-3">{{ item.title }}</strong>
        <span class="text-secondary small">
          {{ item.event_date.strftime('%Y-%m-%d') }}{% if item.end_date and item.end_date != item.event_date %} ~ {{ item.end_date.strftime('%Y-%m-%d') }}{% endif %}
        </span>
        <form method="post" action="/timeline/{{ item.id }}/toggle" class="ms-auto">
          <button class="btn btn-sm btn-link p-0 {% if item.done %}text-success{% else %}text-secondary{% endif %}">
            {% if item.done %}<i class="bi bi-check-circle-fill"></i> 已完成{% else %}<i class="bi bi-circle"></i> 标记完成{% endif %}
          </button>
        </form>
      </div>
      {% if item.description %}<div class="small text-secondary ps-1 mt-1">{{ item.description }}</div>{% endif %}
    </div>
    {% else %}
    <div class="text-center text-secondary py-4">
      <i class="bi bi-calendar-x fs-1"></i><br>暂无时间节点，请先<a href="/import">导入时间线</a>
    </div>
    {% endfor %}
  </div>
</div>

<!-- Add Modal -->
<div class="modal fade" id="addModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <form method="post" action="/timeline/add">
        <div class="modal-header"><h5 class="modal-title">添加节点</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
          <div class="mb-3"><label class="form-label">开始日期 *</label><input type="date" class="form-control" name="event_date" required></div>
          <div class="mb-3"><label class="form-label">结束日期（可选，默认同开始）</label><input type="date" class="form-control" name="end_date"></div>
          <div class="mb-3"><label class="form-label">类型</label>
            <select class="form-select" name="event_type">
              <option value="action">行动项 (Action)</option>
              <option value="deadline">截止日 (Deadline)</option>
              <option value="milestone">里程碑 (Milestone)</option>
              <option value="reminder">提醒 (Reminder)</option>
            </select>
          </div>
          <div class="mb-3"><label class="form-label">标题 *</label><input class="form-control" name="title" required></div>
          <div class="mb-3"><label class="form-label">描述</label><textarea class="form-control" name="description" rows="2"></textarea></div>
        </div>
        <div class="modal-footer"><button class="btn btn-primary">保存</button></div>
      </form>
    </div>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<script>
const items = [
  {% for item in items %}
  {
    id: {{ item.id }},
    title: {{ item.title|tojson }},
    start: {{ item.event_date.strftime('%Y-%m-%d')|tojson }},
    end: {{ (item.end_date or item.event_date).strftime('%Y-%m-%d')|tojson }},
    type: {{ item.event_type|tojson }},
    done: {{ item.done|tojson }},
    description: {{ (item.description or '')|tojson }},
  }{% if not loop.last %},{% endif %}
  {% endfor %}
];

function colorFor(item) {
  if (item.done) return 'rgba(25,135,84,0.5)';
  if (item.type === 'deadline') return '#dc3545';
  if (item.type === 'milestone') return '#ffc107';
  if (item.type === 'reminder') return '#6c757d';
  return '#0d6efd';
}

new Chart(document.getElementById('ganttChart'), {
  type: 'bar',
  data: {
    labels: items.map(i => i.title),
    datasets: [{
      data: items.map(i => [i.start, i.end]),
      backgroundColor: items.map(i => colorFor(i)),
      borderColor: items.map(i => colorFor(i)),
      borderWidth: 1,
      barPercentage: 0.6,
    }]
  },
  options: {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'time',
        time: { unit: 'month', displayFormats: { month: 'yyyy-MM' } },
        ticks: { color: '#aaa' },
        grid: { color: '#2a2a2a' }
      },
      y: {
        ticks: { color: '#aaa' },
        grid: { color: '#1a1a1a' }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => {
            const item = items[ctx.dataIndex];
            return item.description || `${item.start} ~ ${item.end}`;
          }
        }
      }
    },
    onClick: (e, els) => {
      if (els.length > 0) {
        const idx = els[0].index;
        const id = items[idx].id;
        document.getElementById('item-' + id).scrollIntoView({behavior: 'smooth', block: 'center'});
      }
    }
  }
});
</script>
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add templates/timeline.html
git commit -m "feat: rewrite timeline as gantt chart with chart.js"
```

---

## Task 18: 创建 compare.html — Offer 对比表

**Files:**
- Create: `templates/compare.html`

- [ ] **Step 1: 写 compare.html**

Create `templates/compare.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <div class="dashboard-title"><i class="bi bi-trophy me-2 text-primary"></i>Offer 对比表</div>
  <span class="badge bg-primary">{{ offers|length }}</span>
</div>

{% if offers %}
<div class="card">
  <div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
      <thead class="text-secondary small">
        <tr>
          <th>公司</th><th>岗位</th><th>薪资范围</th><th>城市</th><th>行业</th><th>优先级</th><th>状态</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        {% for a in offers %}
        <tr class="{% if a.offer_status=='accepted' %}table-success{% elif a.offer_status=='rejected' %}table-secondary{% elif a.offer_status=='pending' %}table-warning{% endif %}">
          <td><a href="/companies/{{ a.company.id }}" class="text-decoration-none fw-bold">{{ a.company.name }}</a></td>
          <td class="small">{{ a.position or '-' }}</td>
          <td class="small">
            {% if a.salary_min or a.salary_max %}
            {{ a.salary_min or '?' }}-{{ a.salary_max or '?' }}k
            {% else %}-{% endif %}
          </td>
          <td>{{ a.company.city or '-' }}</td>
          <td><span class="badge bg-secondary">{{ a.company.industry or '-' }}</span></td>
          <td><span class="badge badge-priority-{{ a.company.priority }}">{{ a.company.priority }}</span></td>
          <td>
            <span class="badge bg-{{ offer_badges.get(a.offer_status or 'pending', 'secondary') }}">
              {{ offer_labels.get(a.offer_status or 'pending', '待定') }}
            </span>
          </td>
          <td>
            <form method="post" action="/applications/{{ a.id }}/offer_status" class="d-flex gap-1">
              <select name="offer_status" class="form-select form-select-sm" style="width:auto" onchange="this.form.submit()">
                <option value="pending" {% if a.offer_status=='pending' %}selected{% endif %}>待定</option>
                <option value="accepted" {% if a.offer_status=='accepted' %}selected{% endif %}>已接受</option>
                <option value="rejected" {% if a.offer_status=='rejected' %}selected{% endif %}>已拒绝</option>
              </select>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% else %}
<div class="text-center text-secondary py-5">
  <i class="bi bi-trophy fs-1"></i><br>暂无 Offer，加油！
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add templates/compare.html
git commit -m "feat: add offer comparison page"
```

---

## Task 19: 创建 backup.html — 备份恢复页

**Files:**
- Create: `templates/backup.html`

- [ ] **Step 1: 写 backup.html**

Create `templates/backup.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="dashboard-title mb-4"><i class="bi bi-shield-lock me-2 text-primary"></i>备份与恢复</div>

<div class="row g-4">
  <!-- 数据统计 -->
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h6 class="card-title mb-3"><i class="bi bi-database me-2"></i>当前数据</h6>
        <table class="table table-sm">
          {% for k, v in counts.items() %}
          <tr><td class="text-secondary">{{ k }}</td><td class="text-end fw-bold">{{ v }}</td></tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>

  <!-- 导出 -->
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h6 class="card-title mb-3"><i class="bi bi-download me-2"></i>导出备份</h6>
        <p class="text-secondary small">将所有数据导出为 JSON 文件，存到安全位置。</p>
        <form method="post" action="/backup/export">
          <button class="btn btn-primary"><i class="bi bi-download me-1"></i>立即导出</button>
        </form>
      </div>
    </div>
  </div>

  <!-- 恢复 -->
  <div class="col-12">
    <div class="card border-warning">
      <div class="card-body">
        <h6 class="card-title mb-3 text-warning"><i class="bi bi-exclamation-triangle me-2"></i>恢复数据（危险操作）</h6>
        <p class="text-secondary small">上传备份 JSON 文件恢复数据。恢复前会自动备份当前数据库。同名公司可选跳过或覆盖。</p>
        <form method="post" action="/backup/restore" enctype="multipart/form-data">
          <div class="row g-3 align-items-end">
            <div class="col-md-6">
              <label class="form-label">备份文件（JSON）</label>
              <input type="file" class="form-control" name="backup_file" accept=".json" required>
            </div>
            <div class="col-md-3">
              <label class="form-label">同名公司处理</label>
              <select class="form-select" name="mode">
                <option value="skip" selected>跳过（默认）</option>
                <option value="overwrite">覆盖</option>
              </select>
            </div>
            <div class="col-md-3">
              <button class="btn btn-warning w-100"><i class="bi bi-upload me-1"></i>开始恢复</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add templates/backup.html
git commit -m "feat: add backup/restore page"
```

---

## Task 20: 创建 resumes.html — 简历版本列表

**Files:**
- Create: `templates/resumes.html`

- [ ] **Step 1: 写 resumes.html**

Create `templates/resumes.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
  <div class="dashboard-title"><i class="bi bi-file-earmark-person me-2 text-primary"></i>简历版本管理</div>
  <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#uploadModal"><i class="bi bi-plus-lg me-1"></i>上传简历</button>
</div>

<!-- 统计 -->
<div class="row g-3 mb-4">
  <div class="col-md-4">
    <div class="stat-card text-center">
      <div class="num text-white">{{ resumes|length }}</div>
      <div class="small text-secondary">总版本数</div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card text-center">
      <div class="num text-success">{{ default_resume.name if default_resume else '无' }}</div>
      <div class="small text-secondary">默认版本</div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card text-center">
      <div class="num text-info">{{ resumes[0].created_at.strftime('%Y-%m-%d') if resumes else '-' }}</div>
      <div class="small text-secondary">最近上传</div>
    </div>
  </div>
</div>

<!-- 版本卡片 -->
<div class="row g-3">
  {% for r in resumes %}
  <div class="col-md-4">
    <div class="card h-100 {% if r.is_default %}border-success{% endif %}">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            {% if r.file_type == 'pdf' %}
            <i class="bi bi-file-earmark-pdf fs-2 text-danger"></i>
            {% else %}
            <i class="bi bi-file-earmark-word fs-2 text-primary"></i>
            {% endif %}
          </div>
          {% if r.is_default %}<span class="badge bg-success">默认</span>{% endif %}
        </div>
        <h6 class="card-title mt-2 mb-1">{{ r.name }}</h6>
        {% if r.version %}<span class="text-secondary small">{{ r.version }}</span>{% endif %}
        <div class="small text-secondary mt-2">
          {{ r.created_at.strftime('%Y-%m-%d %H:%M') }} · {{ humanize_size(r.file_size or 0) }}
        </div>
        {% if r.note %}<div class="small mt-2 text-secondary">{{ r.note }}</div>{% endif %}
        <div class="mt-3 d-flex flex-wrap gap-1">
          <a href="/resumes/{{ r.id }}/preview" class="btn btn-sm btn-outline-info"><i class="bi bi-eye"></i> 预览</a>
          <a href="/resumes/{{ r.id }}/download" class="btn btn-sm btn-outline-secondary"><i class="bi bi-download"></i></a>
          {% if not r.is_default %}
          <form method="post" action="/resumes/{{ r.id }}/default" class="d-inline">
            <button class="btn btn-sm btn-outline-success"><i class="bi bi-star"></i></button>
          </form>
          {% endif %}
          <button class="btn btn-sm btn-outline-warning" data-bs-toggle="modal" data-bs-target="#editModal-{{ r.id }}"><i class="bi bi-pencil"></i></button>
          <form method="post" action="/resumes/{{ r.id }}/delete" class="d-inline" onsubmit="return confirm('确定删除？')">
            <button class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
          </form>
        </div>
      </div>
    </div>
  </div>
  {% else %}
  <div class="col-12 text-center text-secondary py-5">
    <i class="bi bi-file-earmark-person fs-1"></i><br>暂无简历，点击右上角上传
  </div>
  {% endfor %}
</div>

<!-- Upload Modal -->
<div class="modal fade" id="uploadModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <form method="post" action="/resumes/upload" enctype="multipart/form-data">
        <div class="modal-header"><h5 class="modal-title">上传简历</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
          <div class="mb-3"><label class="form-label">简历文件（PDF/DOCX/DOC，≤20MB）*</label><input type="file" class="form-control" name="file" accept=".pdf,.docx,.doc" required></div>
          <div class="mb-3"><label class="form-label">版本名 *</label><input class="form-control" name="name" placeholder="如：通用版v1、自动化岗位版" required></div>
          <div class="mb-3"><label class="form-label">版本号</label><input class="form-control" name="version" placeholder="如 v1.0"></div>
          <div class="mb-3"><label class="form-label">备注</label><textarea class="form-control" name="note" rows="2" placeholder="适用场景、修改要点等"></textarea></div>
        </div>
        <div class="modal-footer"><button class="btn btn-primary">上传</button></div>
      </form>
    </div>
  </div>
</div>

<!-- Edit Modals -->
{% for r in resumes %}
<div class="modal fade" id="editModal-{{ r.id }}" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <form method="post" action="/resumes/{{ r.id }}/edit">
        <div class="modal-header"><h5 class="modal-title">编辑简历信息</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
          <div class="mb-3"><label class="form-label">版本名</label><input class="form-control" name="name" value="{{ r.name }}"></div>
          <div class="mb-3"><label class="form-label">版本号</label><input class="form-control" name="version" value="{{ r.version or '' }}"></div>
          <div class="mb-3"><label class="form-label">备注</label><textarea class="form-control" name="note" rows="2">{{ r.note or '' }}</textarea></div>
        </div>
        <div class="modal-footer"><button class="btn btn-primary">保存</button></div>
      </form>
    </div>
  </div>
</div>
{% endfor %}
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add templates/resumes.html
git commit -m "feat: add resume version list page"
```

---

## Task 21: 创建 resume_preview.html — 简历预览页

**Files:**
- Create: `templates/resume_preview.html`

- [ ] **Step 1: 写 resume_preview.html**

Create `templates/resume_preview.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <div>
    <a href="/resumes" class="text-decoration-none text-secondary me-2"><i class="bi bi-arrow-left"></i>返回</a>
    <span class="dashboard-title">{{ resume.name }}</span>
    {% if resume.version %}<span class="badge bg-secondary ms-2">{{ resume.version }}</span>{% endif %}
    {% if resume.is_default %}<span class="badge bg-success ms-2">默认</span>{% endif %}
  </div>
  <a href="/resumes/{{ resume.id }}/download" class="btn btn-sm btn-outline-secondary"><i class="bi bi-download me-1"></i>下载原文件</a>
</div>

<div class="card">
  <div class="card-body">
    {% if resume.file_type == 'pdf' %}
    <iframe src="/resumes/{{ resume.id }}/file" style="width:100%; height:80vh; border:0;"></iframe>
    {% elif resume.file_type == 'docx' %}
    <div id="wordContent" class="bg-white text-dark p-4" style="min-height: 80vh;">
      <div class="text-center text-secondary"><div class="spinner-border"></div><br>正在加载 Word 文档...</div>
    </div>
    {% elif resume.file_type == 'doc' %}
    <div class="alert alert-warning">
      <i class="bi bi-exclamation-triangle me-1"></i>不支持预览 .doc 老格式，请<a href="/resumes/{{ resume.id }}/download">下载</a>后查看，或另存为 .docx 后重新上传。
    </div>
    {% else %}
    <div class="alert alert-danger">未知文件类型：{{ resume.file_type }}</div>
    {% endif %}
  </div>
</div>

{% if resume.note %}
<div class="card mt-3">
  <div class="card-body">
    <h6 class="card-title">备注</h6>
    <div class="text-secondary">{{ resume.note }}</div>
  </div>
</div>
{% endif %}
{% endblock %}

{% block scripts %}
{% if resume.file_type == 'docx' %}
<script src="https://cdn.jsdelivr.net/npm/mammoth@1.6/mammoth.browser.min.js"></script>
<script>
fetch('/resumes/{{ resume.id }}/file')
  .then(r => r.arrayBuffer())
  .then(buf => mammoth.convertToHtml({ arrayBuffer: buf }))
  .then(result => {
    document.getElementById('wordContent').innerHTML = result.value || '<p class="text-secondary">（文档内容为空）</p>';
  })
  .catch(err => {
    document.getElementById('wordContent').innerHTML = `<div class="alert alert-danger">预览失败：${err.message}</div>`;
  });
</script>
{% endif %}
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add templates/resume_preview.html
git commit -m "feat: add resume preview page with PDF iframe and Word mammoth"
```

---

## Task 22: 端到端手动验证

**Files:** 无修改，仅验证

- [ ] **Step 1: 启动应用**

Run:
```bash
python app.py
```

Expected: 无报错，`http://127.0.0.1:5000` 可访问。

- [ ] **Step 2: 验证看板**

打开 `http://127.0.0.1:5000/`：
- 城市分布、行业分布饼图正常显示，数量与实际公司数对得上
- 紧急截止横条（如有未来 7 天 deadline）显示
- 面试复盘待写卡片（如有终面/Offer 无评价）显示
- 卡片有阴影，hover 加深

- [ ] **Step 3: 验证公司清单**

打开 `/companies`：
- 表头有"参考薪资"列
- 每行显示薪资或 `-`
- 总条数 badge 显示
- 添加公司 modal 有薪资输入

- [ ] **Step 4: 验证投递记录**

打开 `/applications`：
- 表头有"剩余天数"列
- 截止日期距今天数正确显示，颜色分级
- 总条数显示

- [ ] **Step 5: 验证复习资料 LaTeX**

打开 `/study`，点击任一复习资料：
- `$E=mc^2$` 行内公式正常渲染
- `$$\int_0^1 x\,dx$$` 块级公式正常渲染
- 下标 `$a_b$` 不被 marked.js 破坏

- [ ] **Step 6: 验证时间线甘特图**

打开 `/timeline`：
- 甘特图横向条按日期显示
- 颜色按类型：deadline 红、milestone 黄、action 蓝
- 点击某条滚动到下方列表对应项
- 已完成的条半透明
- 添加节点表单有结束日期输入

- [ ] **Step 7: 验证 Offer 对比**

打开 `/compare`：
- 列出所有 Offer 状态投递（如无则显示空状态）
- 可切换 offer_status
- 行高亮颜色正确

- [ ] **Step 8: 验证面试评价**

打开任一公司详情页：
- 投递记录下方有"添加面试评价"表单
- 填写后提交，评价显示在下方
- 可删除评价

- [ ] **Step 9: 验证备份/恢复**

打开 `/backup`：
- 数据统计正确
- 点击导出，下载 JSON 文件，文件大小 > 0
- 上传该 JSON，恢复成功，flash 显示统计

- [ ] **Step 10: 验证简历上传与预览**

打开 `/resumes`：
- 上传一个 PDF 文件 → 列表显示卡片
- 点击预览 → PDF 在 iframe 显示
- 下载原文件 → 文件正常
- 设为默认 → badge 显示
- 上传一个 DOCX → 预览页 mammoth 转 HTML 显示
- 删除 → 卡片消失

- [ ] **Step 11: 验证移动端**

浏览器开发者工具切到移动端（< 768px）：
- 顶部有汉堡菜单
- 点击汉堡菜单展开 sidebar offcanvas
- 各页面可正常浏览

- [ ] **Step 12: 验证数据未丢**

```bash
python -c "from app import app; from extensions import db; app.app_context().push(); from models import Company, Application, Note, Timeline; print(f'companies={Company.query.count()}, applications={Application.query.count()}, notes={Note.query.count()}, timelines={Timeline.query.count()}')"
```

Expected: 数量与改造前一致。

---

## Task 23: 收尾 — 提交剩余改动

**Files:**
- 可能遗留的 `.gitignore` 更新

- [ ] **Step 1: 更新 .gitignore**

确保 `.gitignore` 包含：
```
data/tracker.db
data/tracker.db.bak.*
data/tracker.db.before_restore.*
data/resumes/
data/backups/
__pycache__/
*.pyc
.pytest_cache/
```

注意：如果之前 `data/tracker.db` 被 track 了，需要 `git rm --cached data/tracker.db`。

- [ ] **Step 2: 检查 git status**

Run:
```bash
git status
```

确认无遗漏文件。

- [ ] **Step 3: 最终提交**

```bash
git add .gitignore
git commit -m "chore: update gitignore for backups and uploads"
```

- [ ] **Step 4: 完成确认**

至此，全部 16 项改造完成。运行 `pytest tests/test_utils.py -v` 确认工具函数测试仍通过。运行 `python app.py` 确认应用正常启动。

---

## 自审清单

**1. Spec 覆盖检查：**
- ✅ 安全（host 127.0.0.1 + SECRET_KEY 环境变量）— Task 8
- ✅ 路径配置化 — Task 2
- ✅ 导入逻辑重写 — Task 7 Step 8
- ✅ 性能（priority 索引 + joinedload + count 合并）— Task 6 / Task 7 Step 2
- ✅ 数据完整性（validate_salary/dates/parse_date）— Task 5
- ✅ 前端（汉堡菜单 + 总条数 + NULL 排序）— Task 11 / Task 7 Step 3
- ✅ 代码组织（拆分）— Task 2-8
- ✅ 备份/恢复 — Task 7 Step 9 + Task 19
- ✅ 面试评价 — Task 7 Step 4 + Task 14
- ✅ Offer 对比 — Task 7 Step 4 + Task 18
- ✅ 截止提醒 — Task 7 Step 2 + Task 12 + Task 15
- ✅ 简历版本 — Task 7 Step 10 + Task 20 + Task 21
- ✅ 甘特图 — Task 7 Step 7 + Task 17
- ✅ LaTeX — Task 16
- ✅ 公司薪资 — Task 6 + Task 13
- ✅ 看板 bug — Task 7 Step 2 + Task 12
- ✅ 前端微调 — Task 11

**2. Placeholder 扫描：** 无 TBD / TODO / "add appropriate"。

**3. 类型一致性：** `parse_date` / `validate_salary` / `validate_dates` 在 utils.py 定义，在 routes 中调用签名一致。`Resume` 模型字段与 `routes/resume.py` 使用一致。`InterviewFeedback` 模型与 `_feedback_form.html` 字段一致。
