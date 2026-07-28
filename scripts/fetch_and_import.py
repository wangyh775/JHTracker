#!/usr/bin/env python3
"""
scripts/fetch_and_import.py — AI 检索结果入库工具

供 company-finder skill 调用，把智能体检索到的公司数据写入：
1. SQLite 数据库（companies 表，跳过已存在的）
2. Markdown 归档（career_data/企业清单_AI_<industry>_<date>.md）

用法：
  # 检查已存在公司名（供 skill 去重）
  python scripts/fetch_and_import.py --check-existing

  # 从 JSON 文件导入
  python scripts/fetch_and_import.py --input /tmp/companies.json

  # 从 stdin 导入（管道）
  cat companies.json | python scripts/fetch_and_import.py --stdin

JSON 格式：
  [
    {
      "name": "汇川技术",
      "industry": "工业自动化",
      "sub_industry": "工控自动化",
      "city": "深圳",
      "job_type": "自动化/机电",
      "match_reason": "伺服系统市占率第一，PID控制经验匹配",
      "website": "https://www.inovance.com"
    }
  ]
"""
import os
import sys
import json
import sqlite3
import re
import argparse
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'tracker.db')
CAREER_DIR = os.path.join(BASE_DIR, 'career_data')


def normalize(name):
    """公司名标准化，用于模糊去重。"""
    if not name:
        return ''
    name = re.sub(r'[（(].*?[）)]', '', name)
    name = name.replace('（中国）', '').replace('有限公司', '').replace('股份', '')
    name = name.replace('集团', '').replace('科技', '').replace('（', '').replace('）', '')
    if '/' in name:
        name = name.split('/')[0]
    return name.strip()


def get_existing_names(cursor):
    """获取所有已存在的公司名（含标准化形式）。"""
    cursor.execute("SELECT name FROM companies")
    raw = [r[0] for r in cursor.fetchall()]
    return set(raw), set(normalize(n) for n in raw if n)


def is_duplicate(new_name, raw_existing, norm_existing):
    """检查是否重复：精确 + 模糊匹配。"""
    if new_name in raw_existing:
        return True
    norm_new = normalize(new_name)
    if not norm_new or len(norm_new) < 2:
        return True
    for en in norm_existing:
        if norm_new in en or en in norm_new:
            return True
    return False


def infer_priority(name):
    """根据公司名推断优先级（简化版，完整版见 constants.py）。"""
    rules = {
        'S': ['拓竹', 'INTAMSYS', '恒泰'],
        'A': ['创想', '纵维', '智能派', '汇川', '大疆'],
    }
    for p, keywords in rules.items():
        if any(kw in name for kw in keywords):
            return p
    return 'B'


def cmd_check_existing():
    """打印已存在的公司名，供 skill 去重。"""
    if not os.path.exists(DB_PATH):
        print("[]", end='')
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM companies ORDER BY name")
    names = [r[0] for r in c.fetchall()]
    print(json.dumps(names, ensure_ascii=False))
    conn.close()


def write_markdown_archive(companies, industry):
    """把本次新增公司追加到 Markdown 归档。"""
    os.makedirs(CAREER_DIR, exist_ok=True)
    today = date.today().strftime('%Y%m%d')
    # 文件名安全化
    safe_industry = re.sub(r'[\\/:*?"<>|]', '_', industry or '未知')
    filename = f'企业清单_AI_{safe_industry}_{today}.md'
    filepath = os.path.join(CAREER_DIR, filename)

    # 同名文件则追加，否则新建
    is_new = not os.path.exists(filepath)
    mode = 'a' if not is_new else 'w'

    with open(filepath, 'a' if not is_new else 'w', encoding='utf-8') as f:
        if is_new:
            f.write(f'# AI 检索公司清单 - {industry or "未知"}\n\n')
            f.write(f'> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
            f.write(f'> 数据来源：company-finder skill\n')
            f.write(f'> 候选人画像：data/profile.md\n\n---\n\n')
            f.write(f'## 一、{industry or "未知"}（共{len(companies)}家）\n\n')
            f.write('| 序号 | 公司名称 | 细分行业 | 城市 | 岗位方向 | 匹配理由 |\n')
            f.write('|:---:|:---------|:---------|:-----|:---------|:---------|\n')
        start_idx = 1
        if not is_new:
            # 续写：读取已有行数估算起始序号
            with open(filepath, 'r', encoding='utf-8') as rf:
                start_idx = sum(1 for line in rf if line.startswith('| ') and '**' in line) + 1

        for i, c in enumerate(companies, start=start_idx):
            name = c.get('name', '').strip()
            sub = c.get('sub_industry', c.get('industry', '')).strip()
            city = c.get('city', '').strip()
            jt = c.get('job_type', '').strip()
            reason = c.get('match_reason', '').strip()
            f.write(f'| {i} | **{name}** | {sub} | {city} | {jt} | {reason} |\n')

    return filepath


def cmd_import(companies_data, source_label='company-finder'):
    """主入库逻辑。"""
    if not isinstance(companies_data, list):
        print(f'❌ JSON 顶层必须是数组，实际是 {type(companies_data).__name__}', file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f'❌ 数据库不存在：{DB_PATH}', file=sys.stderr)
        print('   请先运行 `python app.py` 初始化数据库', file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    raw_existing, norm_existing = get_existing_names(c)

    added = []
    skipped = []
    failed = []

    for item in companies_data:
        name = (item.get('name') or '').replace('**', '').strip()
        if not name:
            failed.append({'name': '', 'error': '公司名为空'})
            continue
        if is_duplicate(name, raw_existing, norm_existing):
            skipped.append(name)
            continue
        try:
            industry = (item.get('industry') or '未知').strip()
            c.execute(
                """INSERT INTO companies
                   (name, industry, city, job_type, match_reason, priority,
                    website, source_list, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    industry,
                    (item.get('city') or '').strip(),
                    (item.get('job_type') or '').strip(),
                    (item.get('match_reason') or '').strip(),
                    infer_priority(name),
                    (item.get('website') or '').strip(),
                    source_label,
                    datetime.now(),
                ),
            )
            conn.commit()
            raw_existing.add(name)
            norm_existing.add(normalize(name))
            added.append(item)
        except sqlite3.IntegrityError:
            skipped.append(name)
        except Exception as e:
            failed.append({'name': name, 'error': str(e)})

    conn.close()

    # 写 Markdown 归档（按 industry 分组）
    archive_files = []
    if added:
        by_industry = {}
        for c in added:
            ind = c.get('industry', '未知')
            by_industry.setdefault(ind, []).append(c)
        for ind, items in by_industry.items():
            fp = write_markdown_archive(items, ind)
            archive_files.append(fp)

    # 汇总报告
    print(json.dumps({
        'added': len(added),
        'skipped': len(skipped),
        'failed': len(failed),
        'archive_files': archive_files,
        'skipped_names': skipped[:20],
        'failed_details': failed[:10],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description='AI 检索结果入库工具')
    parser.add_argument('--check-existing', action='store_true',
                        help='输出已存在公司名 JSON 数组（供 skill 去重）')
    parser.add_argument('--input', help='输入 JSON 文件路径')
    parser.add_argument('--stdin', action='store_true', help='从 stdin 读取 JSON')
    parser.add_argument('--source', default='company-finder',
                        help='source_list 字段标记，默认 company-finder')
    args = parser.parse_args()

    if args.check_existing:
        cmd_check_existing()
        return

    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif args.stdin:
        data = json.load(sys.stdin)
    else:
        parser.print_help()
        sys.exit(1)

    cmd_import(data, source_label=args.source)


if __name__ == '__main__':
    main()
