import sqlite3
import json
import re

def normalize_name(name):
    # Remove anything in parentheses (English names, extra tags)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'（.*?）', '', name)
    # Special cases handling if they have slash
    name = name.split('/')[0]
    return name.strip()

def enrich_from_json(json_path, conn):
    updated_count = 0
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fields = data.get('fields', [])
    try:
        name_idx = fields.index('公司名称')
        website_idx = fields.index('官网')
    except ValueError:
        print(f"Required fields not found in {json_path}")
        return 0

    c = conn.cursor()
    
    for row in data.get('rows', []):
        if not row or len(row) <= max(name_idx, website_idx):
            continue
            
        raw_name = row[name_idx]
        website = row[website_idx]
        
        if not website or website == '无' or 'zhipin.com' in website:
            continue
            
        norm_name = normalize_name(raw_name)
        
        # Fuzzy match in DB
        c.execute("SELECT id, name, website, source_list FROM companies WHERE name LIKE ?", (f"%{norm_name}%",))
        results = c.fetchall()
        
        if results:
            for res in results:
                cid, db_name, db_website, db_source = res
                
                # Check if we should update
                if not db_website or 'zhipin.com' in db_website or 'wecruit.hotjob.cn' in db_website or 'nowcoder.com' in db_website:
                    new_source = db_source
                    if not db_source:
                        new_source = 'JSON导入'
                    elif 'JSON导入' not in db_source:
                        new_source = db_source + ', JSON导入'
                        
                    c.execute("UPDATE companies SET website = ?, source_list = ? WHERE id = ?", (website, new_source, cid))
                    updated_count += 1
                    print(f"Updated: {db_name} -> {website}")

    conn.commit()
    return updated_count

def main():
    db_path = 'D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db'
    conn = sqlite3.connect(db_path)
    
    total_updated = 0
    
    print("Processing records.json...")
    total_updated += enrich_from_json('D:/DJTU/HermesWorkspace/records.json', conn)
    
    print("\nProcessing records_extra.json...")
    total_updated += enrich_from_json('D:/DJTU/HermesWorkspace/records_extra.json', conn)
    
    print(f"\nTotal companies updated: {total_updated}")
    conn.close()

if __name__ == '__main__':
    main()
