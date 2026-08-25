"""Job Hunt Tracker — 应用工厂与启动入口。"""
import os
from flask import Flask
from config import SelectedConfig
from extensions import db, migrate
from constants import STATUS_LIST, INDUSTRIES, CITIES, STATUS_BADGE
from datetime import datetime


def create_app():
    app = Flask(__name__)
    app.config.from_object(SelectedConfig)
    # 把 BASE_DIR 也塞进 config，方便 routes 用
    app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))

    db.init_app(app)
    migrate.init_app(app, db)

    # 启用 SQLite WAL 模式与 busy_timeout，防止多线程/多进程与智能体并发写入锁库
    with app.app_context():
        from sqlalchemy import event
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            cursor.close()

    # 注册所有 blueprint
    from routes import ALL_BLUEPRINTS
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # 上下文处理器：注入全局变量到模板
    @app.context_processor
    def inject_globals():
        from constants import SCALE_CHOICES, FINANCING_STAGE_CHOICES, COMPANY_TYPES
        return dict(
            status_list=STATUS_LIST,
            industries=INDUSTRIES,
            cities=CITIES,
            status_badge=STATUS_BADGE,
            scale_choices=SCALE_CHOICES,
            financing_choices=FINANCING_STAGE_CHOICES,
            company_types=COMPANY_TYPES,
            now=datetime.now,
        )

    return app


app = create_app()


if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data', 'resumes'), exist_ok=True)
    with app.app_context():
        db.create_all()
        # 针对现有 SQLite 数据库自动轻量补全缺失的新列（免全量迁移冲突）
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if 'applications' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('applications')]
            app_alter_cols = {
                'match_score': 'INTEGER',
                'agent_reason': 'TEXT',
                'agent_task_id': 'VARCHAR(100)',
                'source_url': 'VARCHAR(500)',
                'resume_id': 'INTEGER',
                'form_type': 'VARCHAR(50)',
                'source_platform': 'VARCHAR(50)'
            }
            for col_name, col_type in app_alter_cols.items():
                if col_name not in columns:
                    db.session.execute(text(f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}"))
            db.session.commit()
            # 创建全量唯一索引，防止同一公司+同一岗位在任何阶段重复
            try:
                db.session.execute(text("""
                    DROP INDEX IF EXISTS idx_applications_dedup
                """))
                db.session.execute(text("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_applications_dedup
                    ON applications(company_id, LOWER(TRIM(position)))
                """))
                db.session.commit()
            except Exception:
                db.session.rollback()
    # DEBUG 由 SelectedConfig 决定；FLASK_DEBUG=1 仍可强制开启（向后兼容）
    debug = app.config.get('DEBUG', False) or os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='127.0.0.1', port=5000)
