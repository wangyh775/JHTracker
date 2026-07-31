"""投递记录归档业务逻辑。"""
import os
from datetime import datetime, timedelta

from sqlalchemy import and_, or_

from config import DATA_DIR
from extensions import db
from models import Application

LAST_RUN_FILE = os.path.join(DATA_DIR, '.archive_last_run')

# Offer 待定/已接受的不自动归档
_PROTECTED_OFFER = and_(
    Application.status == 'Offer',
    Application.offer_status.in_(['pending', 'accepted']),
)


def get_cutoff(days):
    """返回 cutoff datetime：updated_at 早于此时间的活跃记录可归档。"""
    return datetime.now() - timedelta(days=days)


def query_stale_applications(days):
    """返回满足归档条件且尚未归档的记录列表。"""
    cutoff = get_cutoff(days)
    return Application.query.filter(
        Application.is_archived.is_(False),
        Application.updated_at < cutoff,
        ~_PROTECTED_OFFER,
    ).all()


def archive_applications(apps):
    """批量归档，返回归档条数。"""
    now = datetime.now()
    count = 0
    for app in apps:
        app.is_archived = True
        app.archived_at = now
        count += 1
    if count:
        db.session.commit()
    return count


def archive_one(app_id):
    """归档单条记录，返回是否成功。"""
    app = Application.query.get(app_id)
    if not app or app.is_archived:
        return False
    app.is_archived = True
    app.archived_at = datetime.now()
    db.session.commit()
    return True


def unarchive_one(app_id):
    """恢复单条归档记录，返回是否成功。"""
    app = Application.query.get(app_id)
    if not app or not app.is_archived:
        return False
    app.is_archived = False
    app.archived_at = None
    app.updated_at = datetime.now()
    db.session.commit()
    return True


def run_auto_archive(days, force=False):
    """执行自动归档。force=True 忽略每日节流。返回归档条数。"""
    if not force and not _should_run_today():
        return 0
    count = archive_applications(query_stale_applications(days))
    _touch_last_run()
    return count


def _should_run_today():
    """每天最多自动归档一次。"""
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
