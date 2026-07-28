"""pytest 配置：提供 app / client / db session fixture。

使用内存 SQLite，不污染 data/tracker.db。
"""
import os
import sys
import tempfile
import pytest

# 让 tests/ 能 import 项目根目录的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def app(tmp_path):
    """构造一个使用临时数据库的 app 实例。"""
    # 临时数据目录 + 数据库
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    os.environ['JH_DATA_DIR'] = str(data_dir)
    os.environ['FLASK_ENV'] = 'development'
    os.environ['SECRET_KEY'] = 'test-secret-key-only-for-pytest'

    # 重新导入 config 以读到新的环境变量
    import importlib
    import config
    importlib.reload(config)

    from app import create_app
    from extensions import db

    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SECRET_KEY='test-secret-key-only-for-pytest',
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask 测试客户端。"""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """便捷的 db.session fixture。"""
    from extensions import db
    return db.session
