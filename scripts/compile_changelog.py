#!/usr/bin/env python3
"""
JHTracker 碎片化日志合并脚本 (compile_changelog.py)

功能:
    扫描 `changelog.d/` 目录下的所有碎片 Markdown 文件（忽略 README.md 与 TEMPLATE.md），
    根据 frontmatter 分类解析，格式化后追加写入根目录 `CHANGELOG.md` 对应的版本条目，
    并安全删除已合并的碎片文件。

用法:
    python scripts/compile_changelog.py [--version X.Y.Z] [--dry-run]
"""

import sys
import re
import argparse
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CHANGELOG_DIR = ROOT_DIR / "changelog.d"
CHANGELOG_FILE = ROOT_DIR / "CHANGELOG.md"
VERSION_FILE = ROOT_DIR / "VERSION"

TYPE_MAPPING = {
    "feat": "Features & Enhancements",
    "fix": "Bug Fixes",
    "perf": "Performance Improvements",
    "refactor": "Refactoring",
    "docs": "Documentation",
    "chore": "Maintenance & Tooling",
}


def parse_fragment(file_path: Path):
    content = file_path.read_text(encoding="utf-8").strip()
    meta = {"type": "chore", "title": file_path.stem, "author": "", "issue": ""}
    body = content

    # 简单解析 yaml-like frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.DOTALL)
    if fm_match:
        yaml_text = fm_match.group(1)
        body = fm_match.group(2).strip()
        for line in yaml_text.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                meta[key] = val

    return meta, body


def get_current_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.1.0"


def compile_fragments(target_version: str = None, dry_run: bool = False):
    version = target_version or get_current_version()
    today_str = datetime.now().strftime("%Y-%m-%d")

    fragment_files = [
        f for f in CHANGELOG_DIR.glob("*.md")
        if f.name.upper() not in ("README.MD", "TEMPLATE.MD")
    ]

    if not fragment_files:
        print("[INFO] 没有待合并的碎片日志文件 (changelog.d/ 目录为空或仅包含模板)")
        return 0

    print(f"[*] 发现 {len(fragment_files)} 个变更日志碎片，准备合并至版本 [{version}]...")

    categorized = {k: [] for k in TYPE_MAPPING.keys()}

    for f in fragment_files:
        meta, body = parse_fragment(f)
        c_type = meta.get("type", "chore").lower()
        if c_type not in categorized:
            categorized[c_type] = []

        title = meta.get("title", f.stem)
        author = meta.get("author")
        issue = meta.get("issue")
        suffix = []
        if issue:
            suffix.append(f"#{issue}")
        if author:
            suffix.append(f"by @{author}")
        suffix_str = f" ({', '.join(suffix)})" if suffix else ""

        entry_lines = [f"- **{title}**{suffix_str}"]
        if body:
            for b_line in body.splitlines():
                b_line = b_line.strip()
                if b_line:
                    if not b_line.startswith("-"):
                        entry_lines.append(f"  - {b_line}")
                    else:
                        entry_lines.append(f"  {b_line}")
        categorized[c_type].append("\n".join(entry_lines))

    # 构建 Markdown 片段
    new_section_lines = [f"## [{version}] - {today_str}\n"]
    for c_type, entries in categorized.items():
        if entries:
            section_title = TYPE_MAPPING.get(c_type, c_type.capitalize())
            new_section_lines.append(f"### {section_title}\n")
            for e in entries:
                new_section_lines.append(f"{e}\n")
            new_section_lines.append("")

    new_section_text = "\n".join(new_section_lines).strip() + "\n\n"

    if dry_run:
        print("[DRY RUN] 将会生成的更新日志内容：")
        print("--------------------------------------------------")
        print(new_section_text)
        print("--------------------------------------------------")
        return 0

    # 写入 CHANGELOG.md
    if not CHANGELOG_FILE.exists():
        CHANGELOG_FILE.write_text("# Changelog\n\n", encoding="utf-8")

    current_changelog = CHANGELOG_FILE.read_text(encoding="utf-8")
    
    # 查找第一个 ## [x.y.z] 位置插入在上方，或者直接追加
    first_version_match = re.search(r"^##\s+\[", current_changelog, re.MULTILINE)
    if first_version_match:
        idx = first_version_match.start()
        updated_content = current_changelog[:idx] + new_section_text + current_changelog[idx:]
    else:
        updated_content = current_changelog.rstrip() + "\n\n" + new_section_text

    CHANGELOG_FILE.write_text(updated_content, encoding="utf-8")
    print(f"[OK] 已成功更新 {CHANGELOG_FILE.name} 至版本 [{version}]")

    # 清理已合并的碎片文件
    for f in fragment_files:
        f.unlink()
        print(f"  [DEL] 已清理碎片: {f.name}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="合并 changelog.d 碎片文件至 CHANGELOG.md")
    parser.add_argument("--version", help="指定目标版本号 (默认读取 VERSION 文件)")
    parser.add_argument("--dry-run", action="store_true", help="演练模式，仅打印不写入不删除")
    args = parser.parse_args()

    sys.exit(compile_fragments(args.version, args.dry_run))
