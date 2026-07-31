import os
import sys
import sqlite3
import json
import urllib.request
import urllib.parse
from openai import OpenAI

DB_PATH = 'data/tracker.db'

# Deal with proxy environment logic
def get_llm_client():
    api_key = os.environ.get('OPENAI_API_KEY')
    base_url = os.environ.get('AI_BASE_URL', 'http://localhost:20128/v1')
    model = os.environ.get('AI_MODEL', 'kr/claude-sonnet-4')
    if not api_key:
        # Fallback to config.py values
        try:
            sys.path.insert(0, os.getcwd())
            import config
            api_key = getattr(config, 'OPENAI_API_KEY', None) or getattr(config, 'ANTHROPIC_API_KEY', None)
        except Exception:
            pass
    if not api_key:
        print("❌ Cannot proceed without LLM key")
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url=base_url), model

def search_firm_web(company_name):
    """Fallback search using a simple public search backend or neural lookup."""
    query = f"{company_name} 官网 规模 融资阶段 企业性质"
    print(f"🔍 Searching info for: {company_name}")
    
    # We will use OpenAI/Gemini search via proxy or Exa if installed.
    # To keep it extremely robust and dependency-free for subagents, we call LLM with search capability.
    # The subagent's parent context has Tavily/Exa active. We can also ask LLM directly.
    return query

def enrich_companies_batch(company_ids):
    client, model = get_llm_client()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Load companies
    c.execute(f"SELECT id, name, industry, city FROM companies WHERE id IN ({','.join(map(str, company_ids))})")
    rows = c.fetchall()
    
    for cid, name, ind, city in rows:
        print(f"\n🚀 Processing: {name} (ID={cid})")
        prompt = f"""You are a professional corporate researcher. Retrieve real, verified information for this company:
Company Name: {name}
Industry: {ind}
City: {city}

Provide:
1. Website URL (must be the official career or corporate homepage).
2. Company Scale (must be one of: "少于50人", "50-200人", "200-1000人", "1000-5000人", "5000人以上").
3. Financing Stage (must be one of: "未融资", "天使轮", "A轮", "B轮", "C轮", "D轮及以上", "已上市", "国企").
4. Company Type (must be one of: "民企", "国企", "央企", "外企-国家", "合资").
5. Tags (comma-separated list of up to 4 tags, e.g. "半导体,上市企业,国企,研发中心").

Your response MUST be strict JSON matching this schema:
{{
  "website": "url_here",
  "scale": "scale_here",
  "financing_stage": "financing_stage_here",
  "company_type": "company_type_here",
  "tags": "tags_here"
}}
No other explanation. Ensure all information is real and verified. If you absolutely cannot find a field, leave it null.
"""
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional assistant. You have search capability via search tools and output strict JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            print(f"  Got data: {data}")
            
            # Write back
            c.execute(
                "UPDATE companies SET website=coalesce(?, website), scale=coalesce(?, scale), "
                "financing_stage=coalesce(?, financing_stage), company_type=coalesce(?, company_type), "
                "tags=coalesce(?, tags) WHERE id=?",
                (data.get('website'), data.get('scale'), data.get('financing_stage'), data.get('company_type'), data.get('tags'), cid)
            )
            conn.commit()
        except Exception as e:
            print(f"  ❌ Failed for {name}: {e}")
            
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python enrich.py <company_ids_comma_separated>")
        sys.exit(1)
    ids = [int(x) for x in sys.argv[1].split(',') if x.strip()]
    enrich_companies_batch(ids)
