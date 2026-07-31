import sqlite3, json, os, sys
from openai import OpenAI

DB = 'D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute("SELECT id, name, industry, city, company_type FROM companies WHERE priority='B' AND (scale IS NULL OR scale='') ORDER BY id")
rows = c.fetchall()
print(f"Total remaining: {len(rows)}")

api_key = os.environ.get('OPENAI_API_KEY', 'sk-c4cdcad72c6d4ca48a6dba5ee1a93319')
base_url = os.environ.get('AI_BASE_URL', 'http://localhost:20128/v1')
model = 'kr/claude-sonnet-4'
client = OpenAI(api_key=api_key, base_url=base_url)

BATCH = 50
for batch_start in range(0, len(rows), BATCH):
    batch = rows[batch_start:batch_start+BATCH]
    cb = ''.join(f"{r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4] or ''}\n" for r in batch)
    
    prompt = f"""你是企业信息数据库专家。为每家公司补充：
1. scale: 只能是 "少于50人" "50-200人" "200-1000人" "1000-5000人" "5000人以上"
2. financing_stage: 只能是 "未融资" "天使轮" "A轮" "B轮" "C轮" "D轮及以上" "已上市" "国企"
3. tags: 2-4个逗号分隔标签

格式: id|scale|financing_stage|tags

公司清单:
{cb}

输出{len(batch)}行，严格按id顺序。只输出数据行。"""

    resp = client.chat.completions.create(
        model=model, max_tokens=4000, temperature=0.1,
        messages=[
            {"role": "system", "content": "你是中国工业和企业信息专家。只输出纯数据行。"},
            {"role": "user", "content": prompt}
        ])
    text = resp.choices[0].message.content
    
    cursor = conn.cursor()
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or '|' not in line: continue
        parts = line.split('|')
        if len(parts) >= 4:
            cid_str, scale, fin, tags = parts[0], parts[1], parts[2], '|'.join(parts[3:])
            scale = scale if scale in ["少于50人","50-200人","200-1000人","1000-5000人","5000人以上"] else None
            fin = fin if fin in ["未融资","天使轮","A轮","B轮","C轮","D轮及以上","已上市","国企"] else None
            tags = tags or None
            try:
                cursor.execute("UPDATE companies SET scale=coalesce(?, scale), financing_stage=coalesce(?, financing_stage), tags=coalesce(?, tags) WHERE id=?", (scale, fin, tags, int(cid_str)))
            except: pass
    conn.commit()
    print(f"Batch {batch_start//BATCH+1}: {len(batch)} done")

conn.close()

conn2 = sqlite3.connect(DB)
c2 = conn2.cursor()
c2.execute("SELECT COUNT(*) FROM companies WHERE priority='B' AND (scale IS NULL OR scale='')")
rem = c2.fetchone()[0]
c2.execute("SELECT COUNT(*) FROM companies WHERE scale IS NULL")
tot = c2.fetchone()[0]
c2.execute("SELECT COUNT(*) FROM companies WHERE scale IS NOT NULL")
filled = c2.fetchone()[0]
print(f"\n✅ Remaining B missing scale: {rem}")
print(f"Total still NULL: {tot}")
print(f"Total FILLED: {filled}")
conn2.close()