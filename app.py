"""Job Hunt Tracker — 应用工厂与启动入口。"""
import os
from flask import Flask
from config import Config
from extensions import db, migrate
from constants import STATUS_LIST, INDUSTRIES, CITIES, STATUS_BADGE
from datetime import datetime


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # 把 BASE_DIR 也塞进 config，方便 routes 用
    app.config['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))

    db.init_app(app)
    migrate.init_app(app, db)

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
