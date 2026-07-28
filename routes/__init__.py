"""Blueprint 聚合：所有路由 blueprint 在此导入，供 app 工厂注册。"""
from . import dashboard, company, application, note, study, timeline, import_data, backup, resume, profile

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
    profile.bp,
]
