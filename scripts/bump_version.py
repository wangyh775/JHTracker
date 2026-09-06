#!/usr/bin/env python3
"""
JHTracker 版本统一管理与自动晋级脚本 (bump_version.py)

用法:
    python scripts/bump_version.py check             # 检查各模块版本号是否同步
    python scripts/bump_version.py patch             # 修订号 +1 (如 0.1.0 -> 0.1.1)
    python scripts/bump_version.py minor             # 次版本号 +1 (如 0.1.0 -> 0.2.0)
    python scripts/bump_version.py major             # 主版本号 +1 (如 0.1.0 -> 1.0.0)
    python scripts/bump_version.py set <x.y.z>       # 强制指定版本号
"""

import sys
import re
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT_DIR / "VERSION"
PYPROJECT_FILE = ROOT_DIR / "backend" / "pyproject.toml"
PACKAGE_JSON_FILE = ROOT_DIR / "frontend" / "package.json"


def parse_semver(version_str: str):
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$", version_str.strip())
    if not match:
        raise ValueError(f"无效的语义化版本格式: '{version_str}'，应符合 MAJOR.MINOR.PATCH (例如 0.1.0)")
    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease or ""


def bump_semver(current: str, part: str) -> str:
    major, minor, patch, _ = parse_semver(current)
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"未知的更新类型: {part}. 支持: patch, minor, major")
    return f"{major}.{minor}.{patch}"


def read_current_versions() -> dict:
    versions = {}
    
    # 1. Root VERSION
    if VERSION_FILE.exists():
        versions["VERSION"] = VERSION_FILE.read_text(encoding="utf-8").strip()
    else:
        versions["VERSION"] = None

    # 2. backend/pyproject.toml
    if PYPROJECT_FILE.exists():
        content = PYPROJECT_FILE.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        versions["backend/pyproject.toml"] = match.group(1) if match else None
    else:
        versions["backend/pyproject.toml"] = None

    # 3. frontend/package.json
    if PACKAGE_JSON_FILE.exists():
        try:
            data = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
            versions["frontend/package.json"] = data.get("version")
        except Exception:
            versions["frontend/package.json"] = None
    else:
        versions["frontend/package.json"] = None

    return versions


def update_all_versions(new_version: str):
    parse_semver(new_version)  # 验证合法性

    # 1. 写入 VERSION
    VERSION_FILE.write_text(f"{new_version}\n", encoding="utf-8")
    print(f"  [OK] {VERSION_FILE.relative_to(ROOT_DIR)} -> {new_version}")

    # 2. 更新 backend/pyproject.toml
    if PYPROJECT_FILE.exists():
        pyproject_text = PYPROJECT_FILE.read_text(encoding="utf-8")
        new_pyproject_text = re.sub(
            r'^version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            pyproject_text,
            flags=re.MULTILINE
        )
        PYPROJECT_FILE.write_text(new_pyproject_text, encoding="utf-8")
        print(f"  [OK] {PYPROJECT_FILE.relative_to(ROOT_DIR)} -> {new_version}")

    # 3. 更新 frontend/package.json
    if PACKAGE_JSON_FILE.exists():
        pkg_data = json.loads(PACKAGE_JSON_FILE.read_text(encoding="utf-8"))
        pkg_data["version"] = new_version
        PACKAGE_JSON_FILE.write_text(json.dumps(pkg_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  [OK] {PACKAGE_JSON_FILE.relative_to(ROOT_DIR)} -> {new_version}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    current_versions = read_current_versions()

    print("=" * 60)
    print("JHTracker 版本状态检查:")
    all_matched = True
    base_version = current_versions.get("VERSION")
    for file_path, ver in current_versions.items():
        matched = (ver == base_version) and (ver is not None)
        status = "一致" if matched else "不一致/缺失"
        print(f"  {file_path:<26}: {ver or '未配置'} [{status}]")
        if not matched:
            all_matched = False
    print("=" * 60)

    if cmd == "check":
        if all_matched:
            print(f"所有模块版本完全同步，当前版本为: v{base_version}")
            sys.exit(0)
        else:
            print("警告: 检测到版本不一致，请运行 `python scripts/bump_version.py set <version>` 统一版本！")
            sys.exit(1)

    current_ver = base_version or "0.1.0"
    if cmd in ("patch", "minor", "major"):
        target_ver = bump_semver(current_ver, cmd)
    elif cmd == "set":
        if len(sys.argv) < 3:
            print("错误: set 命令需要提供目标版本号，例如: python scripts/bump_version.py set 0.2.0")
            sys.exit(1)
        target_ver = sys.argv[2]
    else:
        print(f"错误: 未知命令 '{cmd}'\n")
        print(__doc__)
        sys.exit(1)

    print(f"\n执行版本晋级: {current_ver} -> {target_ver} ...")
    update_all_versions(target_ver)
    print(f"\n版本已成功统一更新至: v{target_ver}")
    print("建议执行 Git Tag 命令标记发布:")
    print(f'  git add VERSION backend/pyproject.toml frontend/package.json')
    print(f'  git commit -m "chore(release): bump version to v{target_ver}"')
    print(f'  git tag -a v{target_ver} -m "Release v{target_ver}"')


if __name__ == "__main__":
    main()
