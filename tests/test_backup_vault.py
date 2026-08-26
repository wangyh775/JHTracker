import os
import json
import sqlite3
import pytest
from pathlib import Path
from services.backup_vault import (
    get_backup_root,
    create_db_snapshot,
    create_bundle_backup,
    restore_from_snapshot,
    restore_from_bundle,
    rotate_backups,
    auto_startup_snapshot,
    list_available_backups,
)


@pytest.fixture
def mock_vault_env(tmp_path, monkeypatch):
    """设置临时隔离的 Vault 存储根目录。"""
    vault_dir = tmp_path / "mock_vault"
    monkeypatch.setenv("CAREER_TRACKER_BACKUP_DIR", str(vault_dir))
    return vault_dir


@pytest.fixture
def mock_data_env(tmp_path):
    """创建模拟的工作区 data 目录与数据库。"""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 模拟 SQLite 数据库
    db_file = data_dir / "tracker.db"
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute("CREATE TABLE test_company (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("INSERT INTO test_company (name) VALUES ('Alpha Tech'), ('Beta Corp');")
        conn.commit()

    # 模拟画像与简历
    (data_dir / "profile.md").write_text("# 候选人求职偏好\n- 目标行业: 工业互联网", encoding="utf-8")
    (data_dir / "applicant_profile.json").write_text(json.dumps({"name": "张三", "track": "Embedded"}), encoding="utf-8")
    (data_dir / ".profile_hash").write_text("dummy_hash_123", encoding="utf-8")
    
    resumes_dir = data_dir / "resumes"
    resumes_dir.mkdir()
    (resumes_dir / "resume_embedded.pdf").write_bytes(b"%PDF-1.4 dummy binary content")

    career_dir = tmp_path / "career_data"
    career_dir.mkdir()
    (career_dir / "企业清单_2026.md").write_text("# 核心重点企业\n1. 企业A", encoding="utf-8")

    return {
        "db_file": db_file,
        "data_dir": data_dir,
        "career_dir": career_dir
    }


def test_get_backup_root(mock_vault_env):
    root = get_backup_root()
    assert root == mock_vault_env
    assert (root / "snapshots").is_dir()
    assert (root / "bundles").is_dir()


def test_create_db_snapshot(mock_vault_env, mock_data_env):
    db_file = mock_data_env["db_file"]
    snap = create_db_snapshot(str(db_file), tag="test")
    assert snap is not None
    assert snap.is_file()
    assert "tracker_test_" in snap.name
    assert snap.name.endswith(".db")

    # 验证快照内容一致性
    with sqlite3.connect(str(snap)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM test_company")
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][0] == "Alpha Tech"


def test_create_bundle_backup(mock_vault_env, mock_data_env):
    db_file = mock_data_env["db_file"]
    data_dir = mock_data_env["data_dir"]
    career_dir = mock_data_env["career_dir"]

    bundle = create_bundle_backup(str(db_file), str(data_dir), career_dir=str(career_dir), tag="weekly")
    assert bundle is not None
    assert bundle.is_file()
    assert "bundle_weekly_" in bundle.name
    assert bundle.name.endswith(".zip")

    # 验证 zip 包内部结构
    import zipfile
    with zipfile.ZipFile(bundle, 'r') as zf:
        namelist = zf.namelist()
        assert "tracker.db" in namelist
        assert "profile/profile.md" in namelist
        assert "profile/applicant_profile.json" in namelist
        assert "profile/.profile_hash" in namelist
        assert "resumes/resume_embedded.pdf" in namelist
        assert "career_data/企业清单_2026.md" in namelist
        assert "manifest.json" in namelist


def test_restore_from_snapshot(mock_vault_env, mock_data_env, tmp_path):
    db_file = mock_data_env["db_file"]
    snap = create_db_snapshot(str(db_file), tag="restore_test")
    
    target_restored_db = tmp_path / "restored_tracker.db"
    success = restore_from_snapshot(str(snap), str(target_restored_db))
    assert success is True
    assert target_restored_db.is_file()

    with sqlite3.connect(str(target_restored_db)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM test_company")
        assert cursor.fetchone()[0] == 2


def test_restore_from_bundle(mock_vault_env, mock_data_env, tmp_path):
    db_file = mock_data_env["db_file"]
    data_dir = mock_data_env["data_dir"]
    career_dir = mock_data_env["career_dir"]

    bundle = create_bundle_backup(str(db_file), str(data_dir), career_dir=str(career_dir), tag="restore_bundle")
    
    restore_data_target = tmp_path / "new_data"
    restore_career_target = tmp_path / "new_career"
    
    success = restore_from_bundle(str(bundle), str(restore_data_target), target_career_dir=str(restore_career_target))
    assert success is True
    assert (restore_data_target / "tracker.db").is_file()
    assert (restore_data_target / "profile.md").is_file()
    assert (restore_data_target / "applicant_profile.json").is_file()
    assert (restore_data_target / "resumes" / "resume_embedded.pdf").is_file()
    assert (restore_career_target / "企业清单_2026.md").is_file()


def test_auto_startup_snapshot_throttle(mock_vault_env, mock_data_env):
    db_file = mock_data_env["db_file"]
    data_dir = mock_data_env["data_dir"]

    # 首次执行：成功生成
    snap1 = auto_startup_snapshot(str(db_file), str(data_dir), throttle_hours=2.0)
    assert snap1 is not None
    assert snap1.is_file()

    # 短时间内再次执行：命中节流，返回既有的最新快照文件（或避免重复生成新的不同时间戳快照）
    snap2 = auto_startup_snapshot(str(db_file), str(data_dir), throttle_hours=2.0)
    assert snap2 == snap1


def test_rotate_backups(mock_vault_env, tmp_path):
    snap_dir = mock_vault_env / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    
    # 模拟生成 10 个测试文件
    for i in range(10):
        f = snap_dir / f"snapshot_test_{i:02d}.db"
        f.write_text(f"dummy content {i}")

    # 保留最多 3 个
    deleted = rotate_backups(snap_dir, max_keep=3, max_days=30)
    assert deleted == 7
    remaining = list(snap_dir.glob("snapshot_*.db"))
    assert len(remaining) == 3


def test_list_available_backups(mock_vault_env, mock_data_env):
    db_file = mock_data_env["db_file"]
    data_dir = mock_data_env["data_dir"]

    create_db_snapshot(str(db_file), tag="list1")
    create_bundle_backup(str(db_file), str(data_dir), tag="list2")

    info = list_available_backups()
    assert len(info["snapshots"]) >= 1
    assert len(info["bundles"]) >= 1
    assert "vault_root" in info
