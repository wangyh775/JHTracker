"""用户可定制设置：读写 data/settings.json。"""
import json
import os
from config import DATA_DIR, Config

SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')

_DEFAULTS = {
    'archive_stale_days': Config.ARCHIVE_STALE_DAYS,
    'archive_auto_enabled': Config.ARCHIVE_AUTO_ENABLED,
}


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_settings():
    """读取 settings.json，缺失项用 config 默认值补全。"""
    settings = dict(_DEFAULTS)
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            stored = json.load(f)
        if isinstance(stored, dict):
            settings.update(stored)
    except (OSError, json.JSONDecodeError):
        pass
    settings['archive_stale_days'] = max(1, int(settings.get('archive_stale_days', _DEFAULTS['archive_stale_days'])))
    settings['archive_auto_enabled'] = bool(settings.get('archive_auto_enabled', _DEFAULTS['archive_auto_enabled']))
    return settings


def save_settings(**kwargs):
    """合并写入 settings.json，返回完整设置 dict。"""
    settings = load_settings()
    for key, val in kwargs.items():
        if key in _DEFAULTS:
            settings[key] = val
    settings['archive_stale_days'] = max(1, int(settings['archive_stale_days']))
    settings['archive_auto_enabled'] = bool(settings['archive_auto_enabled'])
    _ensure_data_dir()
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    return settings


def get_archive_stale_days():
    return load_settings()['archive_stale_days']


def is_archive_auto_enabled():
    return load_settings()['archive_auto_enabled']
