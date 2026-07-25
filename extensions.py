"""SQLAlchemy 实例，独立于 app，供 app 工厂初始化。"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
