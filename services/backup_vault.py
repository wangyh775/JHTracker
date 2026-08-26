"""External Data Vault Backup Service.

提供脱离 Git 工作区的外部自动化快照与灾难恢复能力。
核心职责：
1. get_backup_root() — 获取外部备份安全区根目录（默认 ~/.career-tracker/backups/）
2. create_db_snapshot() — 使用 SQLite backup API 在线制作 WAL 事务一致快照
3. create_bundle_backup() — 全量封包（数据库 + 画像 suite + 简历 + career_data）
4. auto_startup_snapshot() — 启动期节流快照（默认 2 小时节流）
5. rotate_backups() — 自动轮转淘汰（保留最近 30 天 / 最多 50 个）
6. detect_disaster_and_recover() — 灾难检测与自愈发现
"""
import glob
import json
import os
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def get_backup_root() -> Path:
    """获取外部备份安全区的根目录。

    默认路径：~/.career-tracker/backups/
    支持环境变量 CAREER_TRACKER_BACKUP_DIR 覆盖。
    """
    env_dir = os.environ.get('CAREER_TRACKER_BACKUP_DIR')
    if env_dir:
        root = Path(env_dir)
    else:
        root = Path.home() / '.career-tracker' / 'backups'
    root.mkdir(parents=True, exist_ok=True)
    (root / 'snapshots').mkdir(parents=True, exist_ok=True)
    (root / 'bundles').mkdir(parents=True, exist_ok=True)
    return root


def get_snapshots_dir() -> Path:
    d = get_backup_root() / 'snapshots'
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_bundles_dir() -> Path:
    d = get_backup_root() / 'bundles'
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_db_snapshot(
    src_db_path: str,
    tag: str = "auto",
    target_dir: Optional[Path] = None
) -> Optional[Path]:
    """使用 sqlite3.backup API 创建事务一致性的纯 DB 在线快照。

    Args:
        src_db_path: 源数据库文件路径（如 data/tracker.db）
        tag: 快照标记（auto / manual / pre_migration）
        target_dir: 目标目录（默认 ~/.career-tracker/backups/snapshots/）

    Returns:
        Path: 生成的快照文件绝对路径，若源文件不存在返回 None
    """
    src_p = Path(src_db_path)
    if not src_p.is_file():
        return None

    dst_dir = target_dir or get_snapshots_dir()
    dst_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_filename = f"tracker_{tag}_{timestamp}.db"
    dst_path = dst_dir / dst_filename

    # 使用 SQLite backup API 确保 WAL 模式下的完整原子性
    with sqlite3.connect(str(src_p)) as src_conn:
        with sqlite3.connect(str(dst_path)) as dst_conn:
            src_conn.backup(dst_conn)

    return dst_path


def create_bundle_backup(
    src_db_path: str,
    data_dir: str,
    career_dir: Optional[str] = None,
    tag: str = "bundle",
    target_dir: Optional[Path] = None
) -> Optional[Path]:
    """制作三位一体全量压缩归档包（DB + 用户画像 + 简历 + 重点企业清单）。

    Args:
        src_db_path: 数据库路径
        data_dir: data 目录路径
        career_dir: career_data 目录路径
        tag: 标签
        target_dir: 目标目录

    Returns:
        Path: 生成的 Zip 文件路径
    """
    src_p = Path(src_db_path)
    if not src_p.is_file():
        return None

    dst_dir = target_dir or get_bundles_dir()
    dst_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"bundle_{tag}_{timestamp}.zip"
    zip_path = dst_dir / zip_filename

    # 先做一个干净的临时 db 快照以避免 WAL 锁
    temp_db = dst_dir / f"temp_{timestamp}.db"
    with sqlite3.connect(str(src_p)) as src_conn:
        with sqlite3.connect(str(temp_db)) as dst_conn:
            src_conn.backup(dst_conn)

    data_p = Path(data_dir)
    manifest = {
        "created_at": datetime.now().isoformat(),
        "tag": tag,
        "files": []
    }

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. 存入 tracker.db
            zf.write(temp_db, arcname="tracker.db")
            manifest["files"].append("tracker.db")

            # 2. 存入用户画像套件
            for fname in ["profile.md", "applicant_profile.json", ".profile_hash"]:
                fpath = data_p / fname
                if fpath.is_file():
                    zf.write(fpath, arcname=f"profile/{fname}")
                    manifest["files"].append(f"profile/{fname}")

            # 3. 存入简历物理文件
            resumes_dir = data_p / "resumes"
            if resumes_dir.is_dir():
                for rfile in resumes_dir.glob("*"):
                    if rfile.is_file():
                        zf.write(rfile, arcname=f"resumes/{rfile.name}")
                        manifest["files"].append(f"resumes/{rfile.name}")

            # 4. 存入重点企业清单
            if career_dir and Path(career_dir).is_dir():
                for cfile in Path(career_dir).glob("*.md"):
                    if cfile.is_file():
                        zf.write(cfile, arcname=f"career_data/{cfile.name}")
                        manifest["files"].append(f"career_data/{cfile.name}")

            # 5. 写入清单信息
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    finally:
        if temp_db.exists():
            try:
                temp_db.unlink()
            except OSError:
                pass

    return zip_path


def rotate_backups(
    max_count: int = 50,
    max_days: int = 30,
    target_dir: Optional[Path] = None,
    **kwargs
) -> int:
    """按数量上限和保留天数自动轮转清理旧快照。

    Returns:
        int: 清理的文件数量
    """
    if "max_keep" in kwargs:
        max_count = kwargs["max_keep"]
    search_dirs = [target_dir] if target_dir else [get_snapshots_dir(), get_bundles_dir()]
    now = time.time()
    deleted_count = 0

    for d in search_dirs:
        if not d.is_dir():
            continue
        files = []
        for f in d.glob("*"):
            if f.is_file() and not f.name.startswith("temp_"):
                files.append(f)

        # 按修改时间从新到旧排序
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for idx, file_path in enumerate(files):
            mtime = file_path.stat().st_mtime
            age_days = (now - mtime) / 86400

            # 超过数量上限 或 超过最大保留天数
            if idx >= max_count or age_days > max_days:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except OSError:
                    pass

    return deleted_count


def auto_startup_snapshot(
    src_db_path: str,
    data_dir: str,
    career_dir: Optional[str] = None,
    throttle_hours: float = 2.0
) -> Optional[Path]:
    """应用启动自检快照：带节流机制。

    如果在 throttle_hours 时间内已存在自动快照，则跳过以避免高频重启冗余。
    """
    src_p = Path(src_db_path)
    if not src_p.is_file():
        return None

    snapshots_dir = get_snapshots_dir()
    recent_snapshots = list(snapshots_dir.glob("tracker_auto_*.db"))

    now = time.time()
    if recent_snapshots:
        recent_snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest = recent_snapshots[0]
        elapsed_hours = (now - latest.stat().st_mtime) / 3600.0
        if elapsed_hours < throttle_hours:
            return latest

    # 触发自动快照
    snap_path = create_db_snapshot(src_db_path, tag="auto")
    # 执行一次轻量轮转
    rotate_backups()
    return snap_path


def list_available_backups() -> Dict[str, List[Dict]]:
    """列出安全区内所有可用的 DB 快照与 Zip 全量包。"""
    snapshots_dir = get_snapshots_dir()
    bundles_dir = get_bundles_dir()

    snapshots = []
    for f in snapshots_dir.glob("*.db"):
        if f.is_file():
            stat = f.stat()
            snapshots.append({
                "filename": f.name,
                "path": str(f.resolve()),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "mtime": stat.st_mtime,
                "type": "db"
            })
    snapshots.sort(key=lambda x: x["mtime"], reverse=True)

    bundles = []
    for f in bundles_dir.glob("*.zip"):
        if f.is_file():
            stat = f.stat()
            bundles.append({
                "filename": f.name,
                "path": str(f.resolve()),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "mtime": stat.st_mtime,
                "type": "bundle"
            })
    bundles.sort(key=lambda x: x["mtime"], reverse=True)

    return {
        "snapshots": snapshots,
        "bundles": bundles,
        "vault_root": str(get_backup_root())
    }


def restore_from_snapshot(
    snapshot_path: str,
    target_db_path: str
) -> bool:
    """从指定的 .db 快照文件恢复到目标数据库。"""
    snap_p = Path(snapshot_path)
    if not snap_p.is_file():
        return False

    target_p = Path(target_db_path)
    target_p.parent.mkdir(parents=True, exist_ok=True)

    # 还原同样使用 SQLite backup API 确保安全写入
    with sqlite3.connect(str(snap_p)) as src_conn:
        with sqlite3.connect(str(target_p)) as dst_conn:
            src_conn.backup(dst_conn)

    return True


def restore_from_bundle(
    bundle_path: str,
    target_data_dir: str,
    target_career_dir: Optional[str] = None
) -> bool:
    """从 Zip 全量包还原整个工作区核心资产。"""
    bundle_p = Path(bundle_path)
    if not bundle_p.is_file():
        return False

    data_p = Path(target_data_dir)
    data_p.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(bundle_p, 'r') as zf:
        for member in zf.namelist():
            if member == "tracker.db":
                zf.extract(member, data_p)
            elif member.startswith("profile/"):
                fname = member.replace("profile/", "")
                if fname:
                    target_file = data_p / fname
                    with zf.open(member) as src, open(target_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)
            elif member.startswith("resumes/"):
                r_dir = data_p / "resumes"
                r_dir.mkdir(parents=True, exist_ok=True)
                fname = member.replace("resumes/", "")
                if fname:
                    target_file = r_dir / fname
                    with zf.open(member) as src, open(target_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)
            elif member.startswith("career_data/") and target_career_dir:
                c_dir = Path(target_career_dir)
                c_dir.mkdir(parents=True, exist_ok=True)
                fname = member.replace("career_data/", "")
                if fname:
                    target_file = c_dir / fname
                    with zf.open(member) as src, open(target_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)

    return True
