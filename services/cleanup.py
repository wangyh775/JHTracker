"""Agent 轨迹清理业务逻辑：自动过期 + 手动清空。"""
import os
from datetime import datetime, timedelta

from sqlalchemy import text

from config import DATA_DIR
from extensions import db
from models import AgentTask, AgentEvent

LAST_RUN_FILE = os.path.join(DATA_DIR, '.traces_cleanup_last_run')


def cleanup_expired_traces(days=30):
    """删除超过 days 天的 agent_events 及无事件的 agent_tasks。返回删除的 events 条数。"""
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

    # 删除过期 events
    result = db.session.execute(
        text("DELETE FROM agent_events WHERE created_at < :cutoff"),
        {'cutoff': cutoff_str}
    )
    deleted_events = result.rowcount

    # 删除无 events 的 tasks
    db.session.execute(text("""
        DELETE FROM agent_tasks WHERE id NOT IN (
            SELECT DISTINCT task_id FROM agent_events
        )
    """))
    db.session.commit()
    return deleted_events


def clear_all_traces():
    """清空所有 agent_events 和 agent_tasks。"""
    AgentEvent.query.delete()
    AgentTask.query.delete()
    db.session.commit()


def run_auto_cleanup(days=30, force=False):
    """执行自动清理。force=True 忽略每日节流。返回清理的 events 条数。"""
    if not force and not _should_run_today():
        return 0
    count = cleanup_expired_traces(days)
    _touch_last_run()
    return count


def _should_run_today():
    """每天最多自动清理一次。"""
    try:
        with open(LAST_RUN_FILE, 'r', encoding='utf-8') as f:
            last = f.read().strip()
        return last != datetime.now().strftime('%Y-%m-%d')
    except OSError:
        return True


def _touch_last_run():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LAST_RUN_FILE, 'w', encoding='utf-8') as f:
        f.write(datetime.now().strftime('%Y-%m-%d'))