"""
scripts/clean_db_fields.py
全量岗位数据库字段清洗与质量修复脚本。
修复项包括：
1. WonderCV 过长导语型标题（title）精简化提取；
2. 非标准学历要求（education_req）归一化映射；
3. 行业分类（industry）中混入的企业性质剥离并归入 type_tags；
4. 非法 chrome-error:// 网申链接安全处理；
5. 非日期型截止时间（deadline，如“招满即止”）规范化为 None 并记录标签；
6. 同步刷新 FTS5 全文索引 jobs_fts。
"""
import sys
import os
import sqlite3
import argparse
import re
import json

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def normalize_education(edu_str: str) -> str:
    """学历要求归一化"""
    if not edu_str:
        return "不限"
    s = str(edu_str).strip()
    if "博士" in s:
        return "博士"
    if "硕" in s or "研究生" in s:
        return "硕士"
    if "本" in s:
        return "本科"
    if "专" in s:
        return "大专"
    return "不限"

def extract_concise_title(company: str, raw_title: str) -> str:
    """从长导语型新闻标题中提取精简岗位/招聘标题"""
    if not raw_title or len(raw_title) <= 25:
        return raw_title
    
    # 按照第一逗号、句号、感叹号、分号切割
    parts = re.split(r'[，。！？；\n]', raw_title)
    if parts:
        first_clause = parts[0].strip()
        # 如果第一句话有意义且在合理长度内 (8~40字)
        if 6 <= len(first_clause) <= 40:
            return first_clause
    
    return raw_title[:35]

def clean_database(db_path: str = "data/public_jobs.db", dry_run: bool = False):
    if not os.path.exists(db_path):
        print(f"[Error] 数据库不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, company, location, industry, type_tags, education_req, detail_url, deadline, description, source_site
        FROM jobs
    """)
    rows = cursor.fetchall()
    total_jobs = len(rows)
    print(f"[*] 全量读取岗位数据: {total_jobs} 条")

    updated_records = []

    for r in rows:
        jid, title, comp, loc, ind, tags_str, edu, url, deadline, desc, src = r
        modified = False

        # 1. 标题清洗（针对 wondercv 等新闻导语式标题）
        new_title = title
        if src == "wondercv" and len(title) > 25:
            candidate_title = extract_concise_title(comp, title)
            if candidate_title != title:
                new_title = candidate_title
                modified = True

        # 2. 学历归一化
        new_edu = edu
        if edu and (len(edu) > 6 or any(k in edu for k in ["统招", "国家", "学历", "全日制"])):
            norm_edu = normalize_education(edu)
            if norm_edu != edu:
                new_edu = norm_edu
                modified = True

        # 3. 行业分类剥离企业性质
        new_ind = ind
        try:
            current_tags = json.loads(tags_str) if tags_str else []
            if not isinstance(current_tags, list):
                current_tags = []
        except Exception:
            current_tags = []
        
        nature_kws = ["民企", "上市公司", "央企", "国企", "外企", "民营企业"]
        if ind in nature_kws:
            if ind not in current_tags:
                current_tags.append(ind)
            new_ind = "其他/综合"
            modified = True

        # 4. 非法协议 URL 清洗
        new_url = url
        if url and not url.startswith(("http://", "https://")):
            new_url = ""
            modified = True

        # 5. 非标准截止时间处理
        new_deadline = deadline
        if deadline and not re.match(r'^\d{4}-\d{2}-\d{2}$', str(deadline).strip()):
            new_deadline = None
            if "招满" in str(deadline) and "招满即止" not in current_tags:
                current_tags.append("招满即止")
            modified = True

        new_tags_str = json.dumps(current_tags, ensure_ascii=False)
        if new_tags_str != tags_str:
            modified = True

        if modified:
            updated_records.append((new_title, new_ind, new_tags_str, new_edu, new_url, new_deadline, jid))

    print(f"[*] 发现需要清洗校正的岗位: {len(updated_records)} 条")
    if updated_records:
        print("\n--- 抽样预览前 8 条待更新岗位 ---")
        for rec in updated_records[:8]:
            print(f"ID: {rec[6]} | Title: '{rec[0]}' | Industry: '{rec[1]}' | Edu: '{rec[3]}' | URL: '{rec[4]}' | Deadline: '{rec[5]}'")

    if not dry_run and updated_records:
        print("\n[*] 正在批量写入数据库更新...")
        cursor.executemany("""
            UPDATE jobs
            SET title = ?,
                industry = ?,
                type_tags = ?,
                education_req = ?,
                detail_url = ?,
                deadline = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, updated_records)
        conn.commit()

        print("[*] 正在同步刷新 FTS5 全文索引 jobs_fts...")
        try:
            cursor.execute("DELETE FROM jobs_fts")
            cursor.execute("""
                INSERT INTO jobs_fts(rowid, title, company, location, description)
                SELECT rowid, title, company, location, description FROM jobs
            """)
            conn.commit()
            print("[+] FTS5 全文索引更新完成！")
        except Exception as e:
            print(f"[!] FTS5 更新提示: {e}")

        print(f"[+] 成功清洗校正 {len(updated_records)} 条岗位数据！")
    elif dry_run:
        print("\n[Dry Run] 试运行结束，数据库未发生任何实际变更。")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="全量岗位数据库字段清洗与质量修复工具")
    parser.add_argument("--db", default="data/public_jobs.db", help="数据库文件路径")
    parser.add_argument("--dry-run", action="store_true", help="试运行预览，不实际修改数据库")
    args = parser.parse_args()

    clean_database(db_path=args.db, dry_run=args.dry_run)
