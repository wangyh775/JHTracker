import sqlite3
import re

db_path = r'D:\DJTU\HermesWorkspace\career-tracker\data\tracker.db'

def get_base_name(name):
    """Strip trailing brackets to get base Chinese name.
    BUT keep '（见机器人章节）' variants as separate entries (cross-references)."""
    if '见机器人' in name:
        return name  # keep cross-reference variants separate
    # Strip trailing bracket(s): 汇川技术（Inovance）-> 汇川技术
    base = re.sub(r'[\(（][^)）]*[\)）]\s*$', '', name).strip()
    # Handle cases with multiple trailing brackets like 埃斯顿（ESTUN）-> already handled by regex
    # Re-stripping in case of double brackets
    base = re.sub(r'[\(（][^)）]*[\)）]\s*$', '', base).strip()
    return base

def calculate_completeness_score(company):
    """Higher score = more complete data = keep this one."""
    score = 0
    priority = company['priority']
    score += {'S': 100, 'A': 80, 'B': 60, 'C': 40}.get(priority, 20)
    if company['salary_min'] is not None or company['salary_max'] is not None:
        score += 10
    if company['website']:
        score += 10
    if company['match_reason']:
        score += 10
    if company['industry']:
        score += 5
    if company['city']:
        score += 5
    if company['sub_city']:
        score += 3
    if company['job_type']:
        score += 3
    return score

def main():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM companies ORDER BY name")
    companies = cursor.fetchall()
    print(f"Total companies in DB before dedup: {len(companies)}")

    # Group by base name
    groups = {}
    for c in companies:
        base = get_base_name(c['name'])
        groups.setdefault(base, []).append(dict(c))

    multi_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Duplicate groups to merge: {len(multi_groups)}")
    print(f"Total entries to delete: {sum(len(v)-1 for v in multi_groups.values())}")
    print()

    merged_count = 0
    deleted_count = 0
    total_apps_reassigned = 0
    total_notes_reassigned = 0

    for base_name, group in sorted(multi_groups.items()):
        group_sorted = sorted(group, key=calculate_completeness_score, reverse=True)
        kept = group_sorted[0]
        duplicates = group_sorted[1:]

        print(f"[{merged_count+1}] Merging: '{base_name}'")
        print(f"  KEEP  id={kept['id']:>4}  {kept['name']:<45} P={kept['priority']} score={calculate_completeness_score(kept)}")

        for dup in duplicates:
            # Reassign FK references
            cursor.execute("UPDATE applications SET company_id=? WHERE company_id=?", (kept['id'], dup['id']))
            apps = cursor.rowcount
            cursor.execute("UPDATE notes SET company_id=? WHERE company_id=?", (kept['id'], dup['id']))
            notes = cursor.rowcount
            total_apps_reassigned += apps
            total_notes_reassigned += notes

            # Merge missing fields from duplicate into kept
            updates = {}
            for field in ['industry', 'city', 'sub_city', 'job_type', 'match_reason',
                          'priority', 'website', 'source_list', 'salary_min', 'salary_max']:
                # Only copy if kept is empty and dup has data
                kept_val = kept.get(field)
                dup_val = dup.get(field)
                if not kept_val and dup_val:
                    updates[field] = dup_val
                    kept[field] = dup_val

            if updates:
                set_clause = ", ".join([f"{f}=?" for f in updates])
                vals = list(updates.values()) + [kept['id']]
                cursor.execute(f"UPDATE companies SET {set_clause} WHERE id=?", vals)
                print(f"  MERGED fields from dup: {list(updates.keys())}")

            print(f"  DELETE id={dup['id']:>4}  {dup['name']:<45} P={dup['priority']} score={calculate_completeness_score(dup)} (apps:{apps} notes:{notes})")
            cursor.execute("DELETE FROM companies WHERE id=?", (dup['id'],))
            deleted_count += 1

        merged_count += 1
        print()

    conn.commit()

    cursor.execute("SELECT COUNT(*) as cnt FROM companies")
    final_count = cursor.fetchone()['cnt']
    print("=" * 60)
    print(f"SUMMARY")
    print(f"  Groups merged:      {merged_count}")
    print(f"  Duplicates deleted: {deleted_count}")
    print(f"  Apps reassigned:   {total_apps_reassigned}")
    print(f"  Notes reassigned:  {total_notes_reassigned}")
    print(f"  Final company count: {final_count}")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    main()
