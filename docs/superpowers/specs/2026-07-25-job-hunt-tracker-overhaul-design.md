# Job Hunt Tracker 全面改造设计文档

- **日期**：2026-07-25
- **项目**：career-tracker（求职全流程管理工具）
- **作者**：用户与 AI 协同设计
- **状态**：已确认，待生成实施计划

---

## 1. 背景与目标

现有 career-tracker 应用是 Flask + SQLite + Bootstrap 5 的本地单用户求职管理工具，已积累真实数据需要保留。当前存在安全性、可维护性、健壮性等多类问题，同时用户希望扩展新功能并修复若干使用痛点。

本次改造目标：

1. 修复 7 类既有问题（安全、路径、导入、性能、数据完整性、前端、代码组织）
2. 新增 4 项功能（数据备份/恢复、面试评价记录、Offer 对比表、截止日期提醒）
3. 满足 4 项新需求（时间线改甘特图、LaTeX 公式渲染、公司薪资字段、看板图表 bug 修复）
4. 全程保留现有数据库内容

## 2. 约束与假设

- **本地单用户使用**：不部署到公网或服务器，不加 CSRF/权限/HTTPS 等多用户安全机制
- **数据保留**：现有 `data/tracker.db` 必须保留，所有表结构变更走 Alembic 迁移
- **技术栈不变**：仍用 Flask + SQLAlchemy + SQLite + Bootstrap 5 + Chart.js
- **原始数据源可用**：`D:/DJTU/HermesWorkspace/career/` 下的 markdown 清单依然存在，作为导入兜底
- **OS**：Windows，路径用正斜杠或 `os.path.join` 兼容

## 3. 架构设计

### 3.1 目录结构（重构后）

```
career-tracker/
├── app.py                  # 仅 app 工厂 + 启动入口
├── config.py               # 配置：路径、密钥、常量
├── constants.py            # STATUS_LIST / INDUSTRIES / CITIES / STATUS_BADGE / PRIORITY_RULES
├── extensions.py           # db = SQLAlchemy() 实例化
├── models.py               # 所有数据模型
├── utils.py                # parse_date / try_int / markdown 导入解析
├── routes/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── company.py
│   ├── application.py
│   ├── note.py
│   ├── study.py
│   ├── timeline.py
│   ├── import_data.py      # 避免与 Python 关键字冲突
│   └── backup.py
├── templates/              # 保持现有结构，新增对应模板
├── migrations/             # Flask-Migrate 生成的迁移脚本
├── data/
│   └── tracker.db
├── requirements.txt
└── README.md
```

### 3.2 模块职责

| 模块 | 职责 | 依赖 |
|---|---|---|
| `config.py` | 集中所有可配置项：DB URI、career 目录、SECRET_KEY 来源、分页大小 | 无 |
| `constants.py` | 业务常量：状态列表、行业、城市、徽章颜色映射、优先级规则表 | 无 |
| `extensions.py` | `db = SQLAlchemy()` 单例 | flask_sqlalchemy |
| `models.py` | 所有 ORM 模型定义 | extensions |
| `utils.py` | 日期解析、整数转换、markdown 表格解析器、薪资校验 | 无 |
| `routes/*.py` | 各业务模块路由，每个文件注册自己的 blueprint | models, utils, constants |
| `app.py` | `create_app()` 工厂、注册 blueprint、初始化 db、启动 | 所有 |

### 3.3 应用工厂模式

```python
# app.py
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    
    from routes import dashboard, company, application, note, study, timeline, import_data, backup
    for bp in [dashboard.bp, company.bp, ...]:
        app.register_blueprint(bp)
    
    return app
```

## 4. 数据模型变更

### 4.1 现有模型修改

**Company 表新增字段**：
- `salary_min` Integer — 公司级参考薪资下限（k/月）
- `salary_max` Integer — 公司级参考薪资上限（k/月）
- `name` 加 `unique=True` 约束

**Application 表新增字段**：
- `offer_status` String(20) — 取值 `accepted`/`rejected`/`pending`；未设置时为 NULL（仅当 status=Offer 时有意义）

### 4.2 新增模型

**InterviewFeedback（面试评价）**：
```python
class InterviewFeedback(db.Model):
    __tablename__ = 'interview_feedbacks'
    id            = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    interviewer   = db.Column(db.String(100))         # 面试官姓名/角色
    interview_date = db.Column(db.Date)
    round         = db.Column(db.String(20))          # 一面/二面/终面
    difficulty    = db.Column(db.Integer)             # 1-5 难度
    self_rating   = db.Column(db.Integer)             # 1-5 自评
    questions     = db.Column(db.Text)                # 问题记录
    improvement   = db.Column(db.Text)                # 改进点
    created_at    = db.Column(db.DateTime, default=datetime.now)
    
    application = db.relationship('Application', backref='feedbacks')
```

### 4.3 迁移策略

- 引入 `Flask-Migrate`（基于 Alembic）
- 初始化：`flask db init` → `flask db stamp head`（标记当前数据库为基线，不生成空迁移）
- 之后每次模型变更：`flask db migrate -m "..."` 生成迁移脚本 → 人工审阅 → `flask db upgrade`
- 集中迁移（一次涵盖本次所有字段变更）：`flask db migrate -m "add company salary, application offer_status, interview_feedback, timeline end_date"`
- 新字段对老数据：salary 字段为 NULL（前端显示 `-`），offer_status 为 NULL，end_date 为 NULL（前端用 event_date 兜底）
- 迁移前先备份 `data/tracker.db` 到 `data/tracker.db.bak.<timestamp>`

## 5. 修复方案详解

### 5.1 安全（轻量化）

| 项 | 当前 | 修复后 |
|---|---|---|
| host | `0.0.0.0` | `127.0.0.1` |
| SECRET_KEY | 硬编码字符串 | `os.environ.get('SECRET_KEY', 'local-dev-secret-key-2026')` |
| CSRF | 无 | 不加（本地单用户） |
| 权限 | 无 | 不加（本地单用户） |

### 5.2 路径配置化

`config.py`：
```python
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAREER_DIR = os.environ.get('CAREER_DIR', 'D:/DJTU/HermesWorkspace/career')
DB_PATH = os.path.join(BASE_DIR, 'data', 'tracker.db')

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'local-dev-secret-key-2026')
    CAREER_DIR = CAREER_DIR
    COMPANY_FILE_PATTERN = '企业清单_{source}_*.md'
    STUDY_FILE = '面试复习手册_自动化机电工程师.md'
    CODING_FILE = '面试编程题.md'
    PER_PAGE_COMPANIES = 40
    PER_PAGE_APPLICATIONS = 30
    PER_PAGE_NOTES = 30
```

### 5.3 导入逻辑重写

**问题**：当前 [app.py:340-389](file:///d:/DJTU/HermesWorkspace/career-tracker/app.py#L340-389) 按列索引硬解析（`parts[name_idx+1]`），表头变化即崩；优先级靠名字字符串匹配；`except: pass` 吞异常。

**重写方案**（`utils.py`）：
```python
def parse_markdown_table(lines):
    """解析 markdown 表格，返回 (headers, rows)
    每行是 dict: {header: value}
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
        # 去掉首尾空元素
        parts = [p for p in parts if p != '' or (parts.index(p) not in (0, len(parts)-1))]
        # 检测分隔行 |---|---|
        if all(set(p) <= set('-: ') and '-' in p for p in parts):
            continue
        if not headers:
            headers = [p.replace('**','').strip() for p in parts]
            in_table = True
        else:
            if len(parts) == len(headers):
                rows.append(dict(zip(headers, parts)))
    return headers, rows
```

**优先级规则配置化**（`constants.py`）：
```python
PRIORITY_RULES = {
    'S': ['拓竹', 'INTAMSYS', '恒泰'],
    'A': ['创想', '纵维', '智能派', '汇川', '大疆'],
}
# 默认 B

def infer_priority(name):
    for p, keywords in PRIORITY_RULES.items():
        if any(kw in name for kw in keywords):
            return p
    return 'B'
```

**导入流程**（`routes/import_data.py`）：
1. 读 markdown，用 `parse_markdown_table` 解析
2. 按表头名称定位字段（公司名/城市/岗位/匹配理由），找不到字段记录日志跳过该行
3. `name` 用 `Company.query.filter_by(name=name).first()` 去重（依赖唯一约束兜底）
4. 行业从文件名推断，规则放 `constants.INDUSTRY_FROM_FILENAME`
5. 失败行累计返回给用户（flash message），不再 `except: pass`
6. 整个导入用 try/except 包住单文件，单文件失败不影响其他文件

### 5.4 性能

| 项 | 修复 |
|---|---|
| `Company.priority` 索引 | `db.Column(..., index=True)` |
| N+1 修复 | `Application.query.options(joinedload(Application.company))` |
| 看板 count 合并 | 用单条 `group_by(Application.status)` 查询返回所有状态计数，避免多次往返 |

### 5.5 数据完整性

**薪资校验**（`utils.py`）：
```python
def validate_salary(min_v, max_v):
    if min_v is not None and max_v is not None and min_v > max_v:
        raise ValueError(f'薪资下限 {min_v} 不能大于上限 {max_v}')
    return min_v, max_v
```

**日期校验**：
```python
def validate_dates(apply_date, deadline):
    if apply_date and deadline and deadline < apply_date:
        raise ValueError('截止日期不能早于投递日期')
    return apply_date, deadline
```

**parse_date 抛异常**：
```python
def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except ValueError as e:
        raise ValueError(f'日期格式错误: {s!r}，期望 YYYY-MM-DD') from e
```

调用方（路由）用 try/except 捕获，flash 错误信息回显给用户。

### 5.6 前端

- **移动端汉堡菜单**：sidebar 在 `< md` 屏幕改为顶部 collapsed navbar，加汉堡按钮 toggle
- **列表总条数**：分页区显示 `共 X 条`（`companies.total`）
- **NULL priority 排序**：`order_by(Company.priority.is_(None), Company.priority, Company.name)`，NULL 排最后

### 5.7 代码组织

按 3.1 目录结构拆分 `app.py`，每个 routes 文件用 Blueprint 注册：

```python
# routes/company.py
from flask import Blueprint
bp = Blueprint('company', __name__)

@bp.route('/companies')
def company_list():
    ...
```

## 6. 新功能设计

### 6.1 数据备份/恢复

**路由**（`routes/backup.py`）：
- `GET /backup` — 渲染备份页面
- `POST /backup/export` — 导出 JSON，返回 `attachment` 下载
- `POST /backup/restore` — 上传 JSON 文件，恢复数据

**导出格式**：
```json
{
  "version": 1,
  "exported_at": "2026-07-25T12:00:00",
  "companies": [...],
  "applications": [...],
  "notes": [...],
  "study_materials": [...],
  "timelines": [...],
  "interview_feedbacks": [...]
}
```

**恢复策略**：
- 上传 JSON 后先校验 `version` 字段
- 按 `companies → applications → notes → ...` 顺序恢复（外键依赖）
- 恢复表单提供单选「同名公司处理方式」：跳过（默认）/ 覆盖
- 恢复前自动备份当前 db 到 `data/tracker.db.before_restore.<timestamp>`
- 恢复完成后跳转到 `/backup` 并 flash 恢复统计（新增 X 家公司、Y 条投递等）

**模板**：新增 `templates/backup.html`

### 6.2 面试评价记录

**路由**（并入 `routes/application.py`）：
- `POST /applications/<a_id>/feedback/add` — 添加评价
- `POST /applications/<a_id>/feedback/<f_id>/delete` — 删除评价

**展示位置**：
- `templates/company_detail.html` 的 Application 详情区块内联展示该投递的所有评价
- 看板加"面试复盘待写"卡片：列出 `status in (一面,二面,终面,Offer)` 且无评价的 Application

**模板**：新增 `templates/_feedback_form.html` 局部模板（可复用）

### 6.3 Offer 对比表

**路由**（`routes/application.py`）：
- `GET /compare` — 渲染对比页

**逻辑**：
- 查询所有 `status='Offer'` 的 Application，带 Company 信息
- 按 `salary_max` 降序排序
- 列：公司名 / 岗位 / 薪资范围 / 城市 / 行业 / 优先级 / offer_status

**offer_status 修改**：
- `POST /applications/<a_id>/offer_status` — 更新 offer_status（accepted/rejected/pending）

**模板**：新增 `templates/compare.html`，对比表用颜色高亮：
- 已接受 → 绿色行
- 已拒绝 → 灰色行
- 待定 → 黄色行

### 6.4 截止日期提醒

**Application 列表**（`templates/applications.html`）：
- 新增"剩余天数"列
- 计算：`deadline - today`
- 显示规则：
  - 已过期 → 红色"已过期 X 天"
  - ≤3 天 → 橙色"剩 X 天"
  - ≤7 天 → 黄色"剩 X 天"
  - >7 天 → 灰色"剩 X 天"
  - 无 deadline → 显示 `-`

**看板顶部紧急横条**（`templates/dashboard.html`）：
- 查询 `Application.deadline` 在未来 7 天内且未到 Offer/已拒状态的
- 横条形式显示，超过 5 条折叠

## 7. 新增需求详解

### 7.1 时间线 → 甘特图

**数据模型变更**：Timeline 表新增 `end_date` 字段（可选，默认等于 event_date，表示单日事件）

**路由**（`routes/timeline.py`）：
- `GET /timeline` — 渲染甘特图 + 列表
- 现有 add/toggle 路由不变，add 表单加 `end_date` 输入

**前端**（`templates/timeline.html`）：
- 引入 `chartjs-adapter-date-fns`
- 用 Chart.js `type: 'bar'` + `indexAxis: 'y'`（横向）
- 每个事件一个 bar，x 轴是时间，颜色按 `event_type`：
  - deadline → `#dc3545`
  - milestone → `#ffc107`
  - action → `#0d6efd`
  - reminder → `#6c757d`
  - 已完成 → 半透明绿色 `rgba(25,135,84,0.5)`
- bar 上 hover 显示 description
- 下方保留列表形式，作为细节补充
- 双向锚点联动：列表项加 `id="item-{{item.id}}"`；甘特图点击事件 `window.location.hash = '#item-' + id`，平滑滚动到列表对应项

**配置**：
```javascript
{
  type: 'bar',
  data: {
    labels: items.map(i => i.title),
    datasets: [{
      data: items.map(i => [i.start_date, i.end_date]),
      backgroundColor: items.map(i => colorFor(i)),
    }]
  },
  options: {
    indexAxis: 'y',
    scales: {
      x: { type: 'time', time: { unit: 'month' } }
    },
    plugins: { tooltip: { callbacks: { label: (ctx) => items[ctx.dataIndex].description } } }
  }
}
```

### 7.2 LaTeX 公式渲染

**模板修改**（`templates/study_content.html`）：

引入 KaTeX CSS + JS + auto-render：
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
```

**渲染流程**：
1. marked.js 先解析 markdown 为 HTML
2. 调用 `renderMathInElement(document.getElementById('content'), {...})` 渲染公式
3. 配置：
```javascript
renderMathInElement(elem, {
  delimiters: [
    {left: '$$', right: '$$', display: true},
    {left: '$', right: '$', display: false},
    {left: '\\(', right: '\\)', display: false},
    {left: '\\[', right: '\\]', display: true}
  ],
  throwOnError: false
});
```

**注意**：marked.js 会把 `_` 解释为斜体，破坏 LaTeX 下标。需要在 marked 解析前对 `$...$` 内的内容做转义保护，或使用 marked 的扩展机制 `marked.use({ extensions: [...] })` 注册 math block。

### 7.3 公司薪资字段

**模型变更**：见 4.1

**模板修改**：

`templates/companies.html`：
- 表头加"参考薪资"列
- 每行显示 `{{ c.salary_min }}-{{ c.salary_max }}k` 或 `-`
- 添加/编辑公司 modal 加两个数字输入

`templates/company_detail.html`：
- 顶部信息块显示公司级参考薪资
- 投递记录表显示每次投递的具体薪资
- 汇总：如果该公司有多条投递，显示"投递薪资范围：X-Yk"

**校验**：用 5.5 的 `validate_salary`

### 7.4 看板图表 bug 修复

**根因**：
1. [app.py:120-123](file:///d:/DJTU/HermesWorkspace/career-tracker/app.py#L120-123) 的 `filter(Company.city!='')` 在 SQLite 中对 NULL 返回 False（NULL != '' 结果是 NULL，被 filter 排除），但同时 NULL 也会被 `group_by` 单独分组为 None
2. [dashboard.html:157](file:///d:/DJTU/HermesWorkspace/career-tracker/templates/dashboard.html#L157) 的 `backgroundColor` 只有 7 个颜色，超过 7 个分类就透明
3. 数据未按数量降序，小块挤一起

**修复**：

后端：
```python
city_counts = db.session.query(
    func.coalesce(Company.city, '未知'), func.count(Company.id)
).filter(
    db.or_(Company.city.is_(None), Company.city != '')
).group_by(Company.city).order_by(func.count(Company.id).desc()).all()
```
（注：上面 `filter` 表达式实际语义是"city 为 NULL 或 city 不等于空字符串"，应写为 `db.or_(Company.city.is_(None), Company.city != '')`，但 SQLite 中 `NULL != ''` 为 NULL 会被排除——更稳妥的写法是 `func.coalesce(Company.city, '') != ''`，即先把 NULL 转空串再过滤。最终代码用后者。）

前端：
```javascript
const palette = ['#0d6efd','#6f42c1','#fd7e14','#20c997','#dc3545','#ffc107','#198754','#0dcaf0','#d63384','#adb5bd','#6610f2','#e9ecef','#fd7e14','#20c997','#6c757d'];
// 循环取色
backgroundColor: data.map((_, i) => palette[i % palette.length])
```

## 8. 路由清单（最终）

| 路径 | 方法 | 模块 | 说明 |
|---|---|---|---|
| `/` | GET | dashboard | 看板 |
| `/companies` | GET | company | 列表 |
| `/companies/<id>` | GET | company | 详情 |
| `/companies/add` | POST | company | 添加 |
| `/companies/<id>/edit` | POST | company | 编辑 |
| `/companies/<id>/delete` | POST | company | 删除 |
| `/applications` | GET | application | 列表 |
| `/applications/add` | POST | application | 添加 |
| `/applications/<id>/status` | POST | application | 改状态 |
| `/applications/<id>/offer_status` | POST | application | 改 offer 状态 |
| `/applications/<id>/delete` | POST | application | 删除 |
| `/applications/<id>/feedback/add` | POST | application | 加评价 |
| `/applications/<id>/feedback/<fid>/delete` | POST | application | 删评价 |
| `/compare` | GET | application | Offer 对比 |
| `/notes` | GET/POST | note | 列表/添加 |
| `/notes/<id>/delete` | POST | note | 删除 |
| `/study` | GET | study | 列表 |
| `/study/<id>/content` | GET | study | 内容 |
| `/study/<id>/toggle` | POST | study | 标记已学 |
| `/timeline` | GET | timeline | 甘特图 |
| `/timeline/add` | POST | timeline | 添加 |
| `/timeline/<id>/toggle` | POST | timeline | 完成切换 |
| `/import` | GET | import_data | 导入页 |
| `/import/companies` | POST | import_data | 导入公司 |
| `/import/study` | POST | import_data | 导入复习 |
| `/import/timeline` | POST | import_data | 导入时间线 |
| `/backup` | GET | backup | 备份页 |
| `/backup/export` | POST | backup | 导出 |
| `/backup/restore` | POST | backup | 恢复 |
| `/api/stats` | GET | dashboard | API |
| `/api/companies/search` | GET | company | API |

## 9. 依赖更新

`requirements.txt` 新增：
```
Flask-Migrate>=4.0
python-dateutil>=2.8  # 已有
```

前端 CDN 新增：
- KaTeX 0.16.9（CSS + JS + auto-render）
- chartjs-adapter-date-fns 3.0

## 10. 测试策略

本地单用户项目不强制写单元测试，但以下关键路径需要手动验证：

1. **迁移**：备份 db → 跑迁移 → 老数据不丢 → 新字段为 NULL 显示 `-`
2. **导入**：用现有 career/ markdown 重新导入，去重生效，失败行有提示
3. **看板图表**：城市/行业分布数量与实际公司数对得上，无 NULL 占大头
4. **LaTeX**：打开复习资料，`$E=mc^2$` 和 `$$\int_0^1 x\,dx$$` 正常渲染
5. **甘特图**：时间线条按日期正确显示，已完成半透明
6. **薪资**：公司列表显示薪资，min>max 校验生效
7. **备份/恢复**：导出 JSON 文件大小 > 0，恢复后数据一致
8. **Offer 对比**：多个 Offer 横向对比，offer_status 可切换
9. **截止提醒**：未来 7 天 deadline 在看板顶部显示

## 11. 实施顺序

1. **基础设施**：拆分 app.py → config/constants/extensions/models/utils + routes/，确保现有功能跑通
2. **引入 Flask-Migrate**：init + 第一次迁移（仅基础结构）
3. **数据完整性修复**：parse_date / validate_salary / validate_dates
4. **看板 bug 修复**：filter NULL + palette 扩展
5. **公司薪资字段**：迁移 + 模型 + 模板
6. **导入逻辑重写**：parse_markdown_table + PRIORITY_RULES
7. **时间线甘特图**：Timeline 加 end_date + 迁移 + 模板
8. **LaTeX 渲染**：study_content.html 引入 KaTeX
9. **面试评价记录**：InterviewFeedback 模型 + 迁移 + 路由 + 模板
10. **Offer 对比表**：offer_status 字段 + 迁移 + /compare 路由 + 模板
11. **截止日期提醒**：applications.html 列 + 看板横条
12. **数据备份/恢复**：backup 路由 + 模板
13. **前端清理**：移动端汉堡菜单 + 列表总条数 + NULL 排序
14. **安全收尾**：host 改 127.0.0.1 + SECRET_KEY 环境变量

## 12. 风险与回滚

- **迁移失败**：迁移前手动备份 `data/tracker.db` 到 `data/tracker.db.bak`，失败时关闭服务 → 覆盖回 .bak → 删除 migrations/ → 重新规划
- **拆分后导入异常**：拆分阶段先不动业务逻辑，纯结构搬运，跑通后再改逻辑
- **KaTeX 与 marked 冲突**：marked 解析 `$a_b$` 时 `_` 被吃成斜体。预案：用 marked 扩展注册 math block，或预处理把 `$...$` 替换为占位符再还原
- **Chart.js time 轴**：必须引入 `chartjs-adapter-date-fns`，否则图表不渲染。预案：CDN 失败时降级为纯 CSS 表格甘特图

## 13. 非目标（YAGNI）

明确不做的事：

- 不加用户系统/权限/CSRF
- 不加自动单元测试套件
- 不加 Docker 部署
- 不加多语言支持
- 不重写为前端框架（保持 Jinja2 模板）
- 不引入前端构建工具（保持 CDN 引入）
- 不做简历版本管理
- 不做 AI 辅助功能
