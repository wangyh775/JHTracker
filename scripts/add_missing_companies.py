import json
import sqlite3
import datetime

def normalize_name(name):
    # Replace normal brackets with full-width brackets
    return name.replace(" (", "（").replace("(", "（").replace(")", "）")

def infer_priority(name):
    s_keywords = ["拓竹", "Bambu", "INTAMSYS", "恒泰", "Snapmaker", "智元", "逐际动力", "汇川", "雷赛", "大疆", "华为", "地平线", "瑞芯微"]
    a_keywords = ["创想", "Creality", "纵维", "智能派", "先临", "华曙", "铂力特", "汉邦", "易加", "闪铸", "大疆", "海康", "科大讯飞", "正运动", "固高", "中科慧眼", "旷视", "商汤", "经纬恒润", "德赛西威", "中控", "信捷", "维宏", "华中", "科德", "广州数控", "拓斯达", "埃夫特", "新松", "极智嘉", "海柔", "快仓"]
    
    for kw in s_keywords:
        if kw in name:
            return "S"
            
    for kw in a_keywords:
        if kw in name:
            return "A"
            
    return "B"

def main():
    conn = sqlite3.connect('D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db')
    cur = conn.cursor()
    
    # Get existing companies
    cur.execute("SELECT name FROM companies")
    existing_companies = {row[0] for row in cur.fetchall()}
    
    files_to_process = [
        'D:/DJTU/HermesWorkspace/records.json',
        'D:/DJTU/HermesWorkspace/records_extra.json'
    ]
    
    added_companies = []
    
    for filepath in files_to_process:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        fields = data.get('fields', [])
        rows = data.get('rows', [])
        
        # Determine index of fields
        try:
            idx_name = fields.index("公司名称")
            idx_industry = fields.index("方向")
            idx_reason = fields.index("备注")
            idx_website = fields.index("官网")
            idx_city = fields.index("城市")
        except ValueError as e:
            print(f"Error in {filepath}: {e}")
            continue
            
        for row in rows:
            name = row[idx_name]
            normalized_name = normalize_name(name)
            
            # Check if exists (with exact or normalized name)
            if normalized_name in existing_companies or name in existing_companies:
                continue
                
            # Need to add
            industry = row[idx_industry]
            city = row[idx_city]
            reason = row[idx_reason]
            website = row[idx_website]
            priority = infer_priority(normalized_name)
            
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cur.execute("""
                INSERT INTO companies 
                (name, industry, city, match_reason, website, priority, source_list, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (normalized_name, industry, city, reason, website, priority, "JSON导入", created_at))
            
            existing_companies.add(normalized_name)
            added_companies.append(normalized_name)
            
    conn.commit()
    conn.close()
    
    print(f"Summary:")
    print(f"Total added: {len(added_companies)}")
    for company in added_companies:
        print(f" - {company}")

if __name__ == "__main__":
    main()
