#!/usr/bin/env python3
"""
enrich_salary.py — Enrich salary data for companies in the career-tracker database.

Sources:
1. match_reason field in DB: parses text like '薪资15-30k', '硕士薪资20-35k', '毕业生薪资15-30k'
2. Markdown source files: 企业清单_A_*.md and 企业清单_B_*.md — parse tables for salary info
3. Hardcoded data from web searches for S/A priority companies (9 total)
"""

import sqlite3
import re
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tracker.db")
MARKDOWN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "career")

# ============================================================
# HARDCODED SALARY DATA from web research (2026 campus recruitment)
# Sources: 猎聘, BOSS直聘, 牛客网, 职友集, 超级简历
# ============================================================
HARDCODED_SALARIES = {
    # S priority
    "拓竹科技": (20, 40),       # 25-40k·15薪 (猎聘); 机械结构30-45k; 校招15k+ 估算20-40k
    "拓竹科技（Bambu Lab）": (20, 40),
    "INTAMSYS": (20, 35),       # 远铸智能: 硕士工资29.7k, 65%岗位20-50k
    "INTAMSYS（远铸智能）": (20, 35),
    "远铸智能": (20, 35),

    # A priority
    "创想三维": (20, 35),        # 猎聘: 20-35k, 运动控制算法专家40-65k
    "创想三维（Creality）": (20, 35),
    "大疆创新": (25, 45),        # 行业标杆, 研发岗25-50k
    "大疆创新（DJI）": (25, 45),
    "智能派": (15, 30),          # 猎聘: 20-40k; 结构15-25k; 校招预估15-30k
    "智能派（Elegoo）": (15, 30),
    "汇川技术": (18, 30),        # 校招研发22k*12-18; 硕士15-30k; 应届生38.7%拿15-30k
    "汇川技术（Inovance）": (18, 30),
    "纵维立方": (18, 30),        # 猎聘: 电机控制25-35k, 结构工程师; 校招18-30k
    "纵维立方（Anycubic）": (18, 30),
}

def get_company_name_variants():
    """Generate name variants for matching hardcoded data."""
    variants = {}
    for name, (min_sal, max_sal) in HARDCODED_SALARIES.items():
        # Also match against simplified names
        simple = re.sub(r'[（(][^)）]*[)）]', '', name).strip()
        variants[name] = (min_sal, max_sal)
        if simple != name:
            variants[simple] = (min_sal, max_sal)
    return variants


def parse_salary_from_markdown(filepath):
    """
    Parse markdown table rows for company names and salary data.
    Returns a dict: {company_name: (salary_min_k, salary_max_k)}
    """
    salary_map = {}
    if not os.path.exists(filepath):
        return salary_map

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: '薪资15-30k', '毕业生薪资15-30k', '硕士薪资20-35k'
    # Pattern 2: '年薪20-30万' → convert to monthly: 万/12*1000/1000 = 万/12
    # We'll handle both k-based and 万-based patterns

    # Find table rows: | num | **company** | ... | match_reason |
    # Then extract salary from the match_reason column
    # A table row looks like: | 3 | **追觅科技（Dreame）** | ... | ... | ... | 高速数字马达...毕业生薪资15-30k... |
    rows = re.findall(r'^\|.*?\|.*?$', content, re.MULTILINE)

    for row in rows:
        cells = [c.strip() for c in row.split('|') if c.strip()]
        if len(cells) < 2:
            continue

        # Skip header/separator rows
        if cells[0].strip('#') in ('', '序号', '#', '---'):
            continue
        first = cells[0].strip()
        if first in ('序号', '#', '---') or first.startswith(':'):
            continue

        # Extract company name from bold markers: **公司名**
        # Try cells[1] (A file format: 序号 | 公司名 | ...) or cells[1] (B file format: # | 公司名 | ...)
        company_cell = None
        match_reason_cell = None

        if len(cells) >= 5:
            # B file format: | # | 公司名 | 行业 | 城市 | 岗位方向 | 匹配理由 |
            # cells[0]=#, cells[1]=公司名, cells[2]=行业, cells[3]=城市, cells[4]=岗位方向, cells[5]=匹配理由
            for i, cell in enumerate(cells):
                # Check if cell looks like a company name (has ** bold markers or Chinese company name)
                if '**' in cell or any(kw in cell for kw in ['公司', '科技', '集团', '技术', '智能', '创新', '电子', '医疗', '动力', '精密', '电气', '机器', '自动化']):
                    if i < len(cells) - 1:  # match_reason is the last column
                        company_cell = cell
                        match_reason_cell = cells[-1]
                        break

        if not company_cell or not match_reason_cell:
            continue

        # Clean company name
        company_name = company_cell.strip('*').strip()
        # Remove markdown bold
        company_name = re.sub(r'\*\*', '', company_name).strip()
        # Remove escaped brackets
        company_name = company_name.strip('*').strip()

        # Skip rows that aren't actually company names
        if len(company_name) < 2 or company_name.isdigit():
            continue

        # Try to extract salary from match_reason
        # Pattern: (\d+)\s*[-~到]\s*(\d+)\s*k
        m = re.search(r'(\d+)\s*[-~\-–到至]\s*(\d+)\s*k', match_reason_cell, re.IGNORECASE)
        if m:
            min_sal = int(m.group(1))
            max_sal = int(m.group(2))
            if min_sal > 0 and max_sal > 0 and min_sal <= max_sal and max_sal <= 200:  # sanity: k range
                salary_map[company_name] = (min_sal, max_sal)
                continue

        # Pattern: 年薪(\d+)\s*[-~]\s*(\d+)\s*万
        m = re.search(r'年薪\s*(\d+)\s*[-~\-–到至]\s*(\d+)\s*万', match_reason_cell)
        if m:
            # Convert 年薪万 to monthly k: 万/年 * 10000 / 12 / 1000 = 万/年 * 0.833
            min_annual = int(m.group(1))
            max_annual = int(m.group(2))
            min_k = round(min_annual / 12 * 10)  # ~万/年 * 0.833 ≈ k/月
            max_k = round(max_annual / 12 * 10)
            if min_k > 0 and max_k > 0 and min_k <= max_k:
                salary_map[company_name] = (min_k, max_k)
                continue

        # Pattern: 月薪(\d+)\s*[-~]\s*(\d+)\s*k
        m = re.search(r'月薪\s*(\d+)\s*[-~\-–到至]\s*(\d+)\s*k', match_reason_cell, re.IGNORECASE)
        if m:
            min_sal = int(m.group(1))
            max_sal = int(m.group(2))
            if min_sal > 0 and max_sal > 0 and min_sal <= max_sal and max_sal <= 200:
                salary_map[company_name] = (min_sal, max_sal)
                continue

    return salary_map


def parse_salary_from_db_match_reason(match_reason):
    """
    Parse salary range from a match_reason string.
    Returns (salary_min_k, salary_max_k) or None.
    """
    if not match_reason:
        return None

    # Pattern: '薪资15-30k', '毕业生薪资15-30k', '硕士薪资20-35k', '月薪12-18k'
    m = re.search(r'(?:薪资|月薪|毕业生薪资|硕士薪资|年薪|校招)?\s*(\d+)\s*[-~\-–到至]\s*(\d+)\s*k', match_reason, re.IGNORECASE)
    if m:
        min_sal = int(m.group(1))
        max_sal = int(m.group(2))
        if min_sal > 0 and max_sal > 0 and min_sal <= max_sal and max_sal <= 200:
            return (min_sal, max_sal)

    # Pattern: '年薪20-30万' → monthly k
    m = re.search(r'年薪\s*(\d+)\s*[-~\-–到至]\s*(\d+)\s*万', match_reason)
    if m:
        min_annual = int(m.group(1))
        max_annual = int(m.group(2))
        min_k = round(min_annual / 12 * 10)
        max_k = round(max_annual / 12 * 10)
        if min_k > 0 and max_k > 0 and min_k <= max_k:
            return (min_k, max_k)

    return None


def find_matching_company(cursor, name_from_md, name_variants):
    """
    Try to match a company name from markdown to a DB company.
    Returns (id, name, priority) or None.
    """
    # Direct match
    cursor.execute("SELECT id, name, priority FROM companies WHERE name = ?", (name_from_md,))
    r = cursor.fetchone()
    if r:
        return r

    # Try matching by removing (**) annotations
    cleaned = re.sub(r'[（(][^)）]*[)）]', '', name_from_md).strip()
    cursor.execute("SELECT id, name, priority FROM companies WHERE name LIKE ?", (f'%{cleaned}%',))
    rows = cursor.fetchall()
    if len(rows) == 1:
        return rows[0]
    elif len(rows) > 1:
        # Prefer exact match
        for r in rows:
            if r[1] == name_from_md:
                return r
        return rows[0]

    return None


def main():
    print("=" * 60)
    print("  Salary Data Enrichment for Career Tracker")
    print("=" * 60)
    print()

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all companies
    c.execute("SELECT id, name, priority, match_reason, salary_min, salary_max FROM companies ORDER BY id")
    companies = c.fetchall()
    print(f"Total companies in DB: {len(companies)}")
    print(f"Companies with NULL salary_min: {sum(1 for r in companies if r['salary_min'] is None)}")
    print()

    # ----------------------------------------------------------
    # Step 1: Parse salary from match_reason in DB
    # ----------------------------------------------------------
    print("--- Step 1: Parsing salary from match_reason in DB ---")
    db_salary_updates = 0
    for row in companies:
        if row['salary_min'] is not None:
            continue  # already has salary

        salary = parse_salary_from_db_match_reason(row['match_reason'])
        if salary:
            min_k, max_k = salary
            c.execute("UPDATE companies SET salary_min = ?, salary_max = ? WHERE id = ?",
                      (min_k, max_k, row['id']))
            db_salary_updates += 1
            print(f"  [DB-match_reason] id={row['id']} {row['name']}: {min_k}-{max_k}k")

    conn.commit()
    print(f"  -> {db_salary_updates} companies updated from match_reason")
    print()

    # ----------------------------------------------------------
    # Step 2: Parse salary from markdown source files
    # ----------------------------------------------------------
    print("--- Step 2: Parsing salary from markdown source files ---")
    md_salary_updates = 0

    # Find markdown files
    md_files = []
    for fname in os.listdir(MARKDOWN_DIR):
        if fname.startswith('企业清单_') and fname.endswith('.md'):
            md_files.append(os.path.join(MARKDOWN_DIR, fname))

    print(f"  Found markdown files: {[os.path.basename(f) for f in md_files]}")

    all_md_salaries = {}
    for fpath in md_files:
        md_salaries = parse_salary_from_markdown(fpath)
        all_md_salaries.update(md_salaries)
        if md_salaries:
            for name, (mn, mx) in md_salaries.items():
                print(f"  [MD] {name}: {mn}-{mx}k (from {os.path.basename(fpath)})")

    # Now try to match markdown companies to DB companies
    name_variants = get_company_name_variants()
    for md_name, (min_sal, max_sal) in all_md_salaries.items():
        match = find_matching_company(c, md_name, name_variants)
        if match:
            db_id, db_name, db_priority = match
            c.execute("SELECT salary_min FROM companies WHERE id = ?", (db_id,))
            existing = c.fetchone()
            if existing and existing[0] is not None:
                # Skip if already has salary from step 1 (or keep the lower bound)
                c.execute("SELECT salary_min, salary_max FROM companies WHERE id = ?", (db_id,))
                cur = c.fetchone()
                new_min = min(cur[0], min_sal) if cur[0] else min_sal
                new_max = max(cur[1], max_sal) if cur[1] else max_sal
                c.execute("UPDATE companies SET salary_min = ?, salary_max = ? WHERE id = ?",
                          (new_min, new_max, db_id))
                print(f"  [MD-match] id={db_id} {db_name}: merged ({cur[0]}-{cur[1]}) + ({min_sal}-{max_sal}) -> ({new_min}-{new_max})")
            else:
                c.execute("UPDATE companies SET salary_min = ?, salary_max = ? WHERE id = ?",
                          (min_sal, max_sal, db_id))
                md_salary_updates += 1
                print(f"  [MD-match] id={db_id} {db_name}: {min_sal}-{max_sal}k")
        else:
            print(f"  [MD-no-match] Could not match '{md_name}' to any DB company")

    # Special case: 追觅科技 has salary in markdown but not in DB match_reason
    # The markdown says "毕业生薪资15-30k" for 追觅科技
    # Let's check if it's already covered
    c.execute("SELECT id, name, salary_min FROM companies WHERE name LIKE '%追觅%'")
    for r in c.fetchall():
        if r[2] is None:
            c.execute("UPDATE companies SET salary_min = 15, salary_max = 30 WHERE id = ?", (r[0],))
            md_salary_updates += 1
            print(f"  [MD-direct] id={r[0]} {r[1]}: 15-30k (from markdown: 毕业生薪资15-30k)")

    conn.commit()
    print(f"  -> {md_salary_updates} companies updated from markdown files")
    print()

    # ----------------------------------------------------------
    # Step 3: Hardcoded salary data for S/A priority companies
    # ----------------------------------------------------------
    print("--- Step 3: Hardcoded salary data for S/A priority companies ---")
    hardcoded_updates = 0
    hardcoded_map = get_company_name_variants()

    c.execute("SELECT id, name, priority, salary_min, salary_max FROM companies WHERE priority IN ('S', 'A')")
    sa_companies = c.fetchall()

    for row in sa_companies:
        db_id = row['id']
        db_name = row['name']
        priority = row['priority']
        cur_min = row['salary_min']
        cur_max = row['salary_max']

        # Skip if already has salary data
        if cur_min is not None:
            print(f"  [SKIP] id={db_id} {db_name} (priority={priority}): already has {cur_min}-{cur_max}k")
            continue

        # Try to find hardcoded salary
        salary = None
        for name_key, sal in hardcoded_map.items():
            if name_key.lower() in db_name.lower() or db_name.lower() in name_key.lower():
                salary = sal
                break

        if salary:
            min_k, max_k = salary
            c.execute("UPDATE companies SET salary_min = ?, salary_max = ? WHERE id = ?",
                      (min_k, max_k, db_id))
            hardcoded_updates += 1
            print(f"  [HARDCODED] id={db_id} {db_name} (priority={priority}): {min_k}-{max_k}k")
        else:
            print(f"  [NO DATA] id={db_id} {db_name} (priority={priority}): no hardcoded salary data found")

    conn.commit()
    print(f"  -> {hardcoded_updates} S/A companies updated from hardcoded data")
    print()

    # ----------------------------------------------------------
    # Summary
    # ----------------------------------------------------------
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    c.execute("SELECT COUNT(*) FROM companies WHERE salary_min IS NOT NULL")
    with_salary = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM companies WHERE salary_min IS NULL")
    without_salary = c.fetchone()[0]

    c.execute("""
        SELECT priority, 
               COUNT(*) as total,
               SUM(CASE WHEN salary_min IS NOT NULL THEN 1 ELSE 0 END) as filled
        FROM companies 
        GROUP BY priority 
        ORDER BY priority
    """)
    print()
    print(f"  Companies with salary data: {with_salary}")
    print(f"  Companies without salary data: {without_salary}")
    print()
    print("  By priority:")
    for row in c.fetchall():
        pct = row['filled'] / row['total'] * 100 if row['total'] > 0 else 0
        print(f"    {row['priority']}: {row['filled']}/{row['total']} ({pct:.1f}%)")

    # Show all companies that now have salary data
    c.execute("""
        SELECT id, name, priority, salary_min, salary_max 
        FROM companies 
        WHERE salary_min IS NOT NULL 
        ORDER BY priority, name
    """)
    print()
    print("  Companies with salary data:")
    for row in c.fetchall():
        print(f"    id={row['id']:>4} [{row['priority']}] {row['name']:<30s} {row['salary_min']}-{row['salary_max']}k")

    conn.close()
    print()
    print("Done!")


if __name__ == "__main__":
    main()