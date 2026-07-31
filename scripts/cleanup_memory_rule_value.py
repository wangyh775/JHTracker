"""
scripts/cleanup_memory_rule_value.py — 清洗 memories 表中被污染的 rule_value

背景：旧版 handle_decision 的 reject 分支存在 bug，把整段 raw_feedback 塞进了 rule_value，
导致负向子串匹配几乎永不命中。本脚本把误存在 rule_value 的长文本移到 raw_feedback
（若 raw_feedback 为空），然后清空 rule_value。

判定规则：rule_value 长度 > 阈值（默认 50 字符）视为被污染的长文本。

用法：
  python scripts/cleanup_memory_rule_value.py             # 预览待清洗条目（默认 dry-run）
  python scripts/cleanup_memory_rule_value.py --apply     # 实际执行清洗
  python scripts/cleanup_memory_rule_value.py --threshold 80  # 自定义长度阈值
"""

import os
import sys
import sqlite3
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR
DB_PATH = os.path.join(DATA_DIR, 'tracker.db')

DEFAULT_THRESHOLD = 50


def find_polluted_records(conn, threshold):
    """查找 rule_value 长度超过阈值的记录。"""
    c = conn.cursor()
    c.row_factory = sqlite3.Row
    c.execute(
        "SELECT id, category, rule_value, raw_feedback FROM memories "
        "WHERE rule_value IS NOT NULL AND LENGTH(rule_value) > ?",
        (threshold,)
    )
    return [dict(r) for r in c.fetchall()]


def main():
    parser = argparse.ArgumentParser(description='清洗 memories 表中被污染的 rule_value（长文本移至 raw_feedback）')
    parser.add_argument('--apply', action='store_true', help='实际执行清洗（默认仅预览）')
    parser.add_argument('--threshold', type=int, default=DEFAULT_THRESHOLD,
                        help=f'rule_value 长度阈值，超过则视为污染（默认 {DEFAULT_THRESHOLD}）')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    records = find_polluted_records(conn, args.threshold)
    if not records:
        print(f"✅ 没有发现 rule_value 长度 > {args.threshold} 的污染记录。")
        conn.close()
        return

    print(f"🔍 发现 {len(records)} 条疑似污染记录（rule_value 长度 > {args.threshold}）：\n")
    for r in records:
        rv_preview = (r['rule_value'] or '')[:80]
        has_feedback = "有" if r['raw_feedback'] else "无"
        print(f"  [id={r['id']}] category={r['category']} | raw_feedback={has_feedback}")
        print(f"         rule_value({len(r['rule_value'] or '')}字): {rv_preview}...")
        print()

    if not args.apply:
        print("📋 以上为预览。加 --apply 实际执行清洗。")
        conn.close()
        return

    cleaned = 0
    skipped = 0
    cursor = conn.cursor()
    for r in records:
        # 若 raw_feedback 已有值，不覆盖（保留原始反馈），仅清空 rule_value
        if r['raw_feedback']:
            cursor.execute(
                "UPDATE memories SET rule_value = '' WHERE id = ?",
                (r['id'],)
            )
            action = "仅清空 rule_value（raw_feedback 已有值，保留）"
        else:
            cursor.execute(
                "UPDATE memories SET raw_feedback = rule_value, rule_value = '' WHERE id = ?",
                (r['id'],)
            )
            action = "rule_value → raw_feedback，清空 rule_value"
        cleaned += 1
        print(f"  [id={r['id']}] ✓ {action}")

    conn.commit()
    print(f"\n✅ 完成！清洗 {cleaned} 条，跳过 {skipped} 条。")
    conn.close()


if __name__ == '__main__':
    main()
