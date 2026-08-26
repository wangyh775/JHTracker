"""SQLAlchemy 实例，独立于 app，供 app 工厂初始化。"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

class SafeSQLAlchemy(SQLAlchemy):
    """带自毁防呆熔断机制的 SQLAlchemy 封装。
    
    在非测试环境中调用 drop_all() 将直接抛出 RuntimeError，防止 Agent 误删生产数据。
    """
    def drop_all(self, *args, **kwargs):
        # 允许在测试环境 (TESTING=True) 或显式环境变量覆盖下执行
        allow_override = os.environ.get('ALLOW_DROP_DB') == 'I_KNOW_WHAT_I_AM_DOING'
        # 检查当前 app 的 TESTING 配置
        is_testing = False
        try:
            from flask import current_app
            is_testing = current_app.config.get('TESTING', False)
        except Exception:
            pass

        if not is_testing and not allow_override:
            raise RuntimeError(
                "CRITICAL: db.drop_all() is strictly FORBIDDEN in non-test environment! "
                "Set ALLOW_DROP_DB=I_KNOW_WHAT_I_AM_DOING if you truly intend to wipe database."
            )
        super().drop_all(*args, **kwargs)

db = SafeSQLAlchemy()
migrate = Migrate()

