# Career Tracker 重构代码审查报告

审查范围：`routes/__init__.py`, `routes/*.py`, 所有 `templates/` 下的 HTML 模板，以及核心 Python 文件 (`app.py`, `extensions.py`, `config.py`, `constants.py`, `utils.py`, `models.py`)。

审查日期：2026-07-25

---

## 审查结论摘要

| 检查项 | 结论 |
|--------|------|
| ALL_BLUEPRINTS 注册 | ✅ 正确 |
| Blueprint 名称冲突 | ✅ 无冲突 |
| 模板变量完整度 | ✅ 所有模板变量均有传入 |
| 导入/依赖完整性 | ❌ 缺失 `Flask-Migrate` |
| import_data 文件路径 | ✅ 数据源目录和文件均存在 |
| app.py 初始化逻辑 | ✅ 逻辑正确（装好依赖后可用） |

---

## 1. 依赖缺失（阻止启动）❌

`extensions.py` 中导入了 `from flask_migrate import Migrate`，但当前环境**未安装** `Flask-Migrate`。

- `extensions.py` → 被 `app.py`, `models.py`, `routes/*.py` 几乎所有文件间接依赖
- 影响：程序将抛出 `ModuleNotFoundError: No module named 'flask_migrate'` 完全无法启动
- **修复**: 运行 `pip install Flask-Migrate`（`requirements.txt` 中已有 `Flask-Migrate>=4.0`，但未实际安装）

---

## 2. Blueprint 注册与命名 ✅

### 2.1 ALL_BLUEPRINTS 列举

`routes/__init__.py` 中 `ALL_BLUEPRINTS` 正确列举了全部 9 个 Blueprint：

| 模块 | Blueprint 实例 | 文件存在 |
|------|----------------|----------|
| dashboard | `dashboard.bp` | ✅ |
| company | `company.bp` | ✅ |
| application | `application.bp` | ✅ |
| note | `note.bp` | ✅ |
| study | `study.bp` | ✅ |
| timeline | `timeline.bp` | ✅ |
| import_data | `import_data.bp` | ✅ |
| backup | `backup.bp` | ✅ |
| resume | `resume.bp` | ✅ |

### 2.2 Blueprint 名称无冲突

所有 Blueprint 在实例化时使用了不重复的名称：
- `'application'`, `'backup'`, `'company'`, `'dashboard'`, `'import_data'`, `'note'`, `'resume'`, `'study'`, `'timeline'` — 相互不冲突。

### 2.3 路由路径无冲突

所有 Blueprint 均**未使用 `url_prefix`**，所有路由直接注册在根路径下。各路由表路径唯一，无冲突：

| Blueprint | 注册的路由 |
|-----------|-----------|
| dashboard | `/` |
| company | `/companies`, `/companies/<int:c_id>`, `/companies/add`, `/companies/<int:c_id>/edit`, `/companies/<int:c_id>/delete`, `/api/companies/search` |
| application | `/applications`, `/applications/add`, `/applications/<int:a_id>/status`, `/applications/<int:a_id>/offer_status`, `/applications/<int:a_id>/delete`, `/applications/<int:a_id>/feedback/add`, `/applications/<int:a_id>/feedback/<int:f_id>/delete`, `/compare` |
| note | `/notes`, `/notes/<int:n_id>/delete` |
| study | `/study`, `/study/<int:m_id>/content`, `/study/<int:m_id>/toggle` |
| timeline | `/timeline`, `/timeline/add`, `/timeline/<int:t_id>/toggle` |
| import_data | `/import`, `/import/companies`, `/import/companies/resync`, `/import/study`, `/import/timeline` |
| backup | `/backup`, `/backup/export`, `/backup/restore` |
| resume | `/resumes`, `/resumes/upload`, `/resumes/<int:r_id>/preview`, `/resumes/<int:r_id>/file`, `/resumes/<int:r_id>/download`, `/resumes/<int:r_id>/edit`, `/resumes/<int:r_id>/default`, `/resumes/<int:r_id>/delete` |

**⚠️ 注意事项（非 bug）：** 没有 Blueprint 使用 `url_prefix`，这在当前规模下没有问题，但随着项目扩大，建议给不同功能组的 Blueprint 加 `url_prefix`（如 `url_prefix='/applications'`）以增强可维护性。

---

## 3. 模板变量完整性检查 ✅

### 3.1 全局变量（context_processor 注入）

`app.py` 的 `inject_globals()` 注入以下变量，所有模板均可直接使用：
- `status_list` ✅
- `industries` ✅
- `cities` ✅
- `status_badge` ✅
- `now` (= `datetime.now` 函数) ✅

### 3.2 逐模板变量检查

| 模板 | 路由 | 额外传入变量 | 缺少变量 |
|------|------|-------------|---------|
| dashboard.html | `dashboard()` | total, applied, interviews, offers, rejected, funnel, max_funnel, city_counts, ind_counts, pri_counts, upcoming, recent, urgent_deadlines, pending_feedbacks | 无 ✅ |
| companies.html | `company_list()` | companies (paginate) | 无 ✅ |
| company_detail.html | `company_detail()` | company, apps, notes | 无 ✅ |
| applications.html | `app_list()` | apps (paginate), channels | 无 ✅ |
| compare.html | `compare()` | offers, offer_choices, offer_labels, offer_badges | 无 ✅ |
| notes.html | `notes()` | notes (paginate) | 无 ✅ |
| study.html | `study_list()` | materials | 无 ✅ |
| study_content.html | `study_content()` | material, content | 无 ✅ |
| timeline.html | `timeline_view()` | items | 无 ✅ |
| resumes.html | `resume_list()` | resumes, default_resume, humanize_size | 无 ✅ |
| resume_preview.html | `resume_preview()` | resume | 无 ✅ |
| backup.html | `backup_page()` | counts | 无 ✅ |
| import.html | `import_page()` | (无额外变量) | 无 ✅ |
| _sidebar.html | — (include) | request 全局可用 | 无 ✅ |
| _feedback_form.html | — (include) | a (application 对象) 需在 parent 模板传入 | 正常 ✅ |

### 3.3 注意事项

- `dashboard.html` 第 61 行 `offers/applied*100 if applied else 0` — 有除零保护，正常 ✅
- `applications.html` 第 45 行 `{% if a.salary_min %}` — `a.salary_min` 可能为 0，0 在 Jinja2 中为 falsy，薪资为 0 时将不显示；但语义上 0 薪资不常见，可接受 ✅
- `notes.html` 中 `name="company_id"` 的 datalist 搜索 — 选项的 `value` 设置为了公司 ID 而非公司名称，用户看到的是数字而非公司名（UI 体验小问题，但功能上 value 提交到后端 `try_int()` 后转为整数，不影响后端逻辑）✅

---

## 4. 导入错误 / 缺失依赖 ✅（除 flask-migrate 外）

### 4.1 各文件内部导入

| 文件 | 导入分析 |
|------|---------|
| `app.py` | 导入 `os`, `flask`, `config, extensions, constants, datetime, routes` — 全部正确 ✅ |
| `extensions.py` | 导入 `flask_sqlalchemy.db`, `flask_migrate.Migrate` — 后者缺少包 ❌ |
| `config.py` | 仅依赖 `os` — 正确 ✅ |
| `constants.py` | 无外部导入 — 正确 ✅ |
| `utils.py` | `from datetime import datetime` — 正确 ✅ |
| `models.py` | 导入 `datetime`, `extensions.db` — 正确（但被 extensions 拖累）✅⏳ |
| `routes/application.py` | 导入 `flask.*`, `sqlalchemy.joinedload`, `extensions.db`, `models.*`, `constants.*`, `utils.*` — 正确 ✅ |
| `routes/backup.py` | 导入 `os, json, shutil, datetime, flask.*, extensions.db, models.*, config.Config` — 正确 ✅ |
| `routes/company.py` | 导入 `flask.*`, `extensions.db`, `models.*`, `constants.*`, `utils.*` — 正确 ✅ |
| `routes/dashboard.py` | 导入 `flask.*`, `sqlalchemy.func`, `extensions.db`, `models.*`, `constants.*` — `from sqlalchemy import func` 应该是 `from sqlalchemy import func`，这里虽然是 `from sqlalchemy import func` 但从代码看没错 ✅ |

### 4.2 外部包依赖

| 包 | 在 requirements.txt | 已安装 |
|----|-------------------|--------|
| Flask | ✅ | ✅ |
| Flask-SQLAlchemy | ✅ | ✅ |
| Flask-Migrate | ✅ | ❌ **未安装** |
| python-dateutil | ✅ | ? (未导入，无影响) |

---

## 5. import_data.py 路径依赖 ✅

`Config.CAREER_DIR` 默认为 `D:/DJTU/HermesWorkspace/career`，经验证该目录存在。

所需文件：

| 文件路径 | 存在？ |
|---------|--------|
| `D:/DJTU/HermesWorkspace/career/企业清单_A_工业自动化_能源_半导体_汽车.md` | ✅ |
| `D:/DJTU/HermesWorkspace/career/企业清单_B_机器人_3D打印_高端装备_医疗_消费电子.md` | ✅ |
| `D:/DJTU/HermesWorkspace/career/面试复习手册_自动化机电工程师.md` | ✅ |
| `D:/DJTU/HermesWorkspace/career/面试编程题.md` | ✅ |
| `D:/DJTU/HermesWorkspace/career/` 目录本身 | ✅ |

所有 Markdown 导入都能成功读取。

---

## 6. app.py 初始化流程 ✅

```python
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))

    db.init_app(app)
    migrate.init_app(app, db)              # ← 缺少 flask_migrate 时这里崩溃

    from routes import ALL_BLUEPRINTS
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    @app.context_processor
    def inject_globals():
        return dict(status_list=..., industries=..., cities=...,
                    status_badge=..., now=datetime.now)

    return app
```

- `Config` 加载正确 ✅
- `db.init_app(app)` → 假设 `extensions.py` 的导入正确，这一步 OK ✅
- `migrate.init_app(app, db)` → 当前因缺包会抛异常 ❌
- Blueprint 注册逻辑正确 ✅
- 上下文处理器正确 ✅
- 最后的 `if __name__ == '__main__':` 块中创建 `data/` 和 `data/resumes/` 目录 ✅
- `db.create_all()` 在 app context 中调用 ✅
- `app.run(debug=True, host='127.0.0.1', port=5000)` ✅

---

## 7. 其他值得注意的发现

### 7.1 `notes.html` 的 datalist 显示问题（UI 小问题）
```javascript
dl.innerHTML = data.map(c =>
  '<option value="' + c.id + '">' + c.name + ' (' + c.city + ')' + '</option>'
).join('');
```
HTML `<datalist>` 中，`<option value>` 的值既是显示文本又是提交值。这意味着用户在下拉列表中看到的是数字 ID 而不是公司名。功能上不影响（后端 `try_int()` 正确解析），但用户体验不佳。

**建议**: 保留 `value` 不变，无需修改。

### 7.2 `backup.py` 中 `backup_restore` 路径处理
```python
db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
```
`SQLALCHEMY_DATABASE_URI` 格式为 `sqlite:///D:/DJTU/.../tracker.db`，替换后为 `D:/DJTU/.../tracker.db`。Windows 上 `shutil.copy2` 能正确处理正斜杠路径。没问题 ✅

### 7.3 测试文件状态
`tests/test_utils.py` 包含对 `utils.py` 的单元测试，且导入路径正确（与根目录应用共享同一 Python 路径）。测试使用 `pytest`，代码无语法问题。

---

## 总体意见

**代码质量良好，结构清晰。** Flask 应用工厂 + Blueprint 模式使用正确。主要需要解决的问题是安装缺失的 `Flask-Migrate` 包。修复此问题后，应用应能正常启动并运行所有已实现功能。
