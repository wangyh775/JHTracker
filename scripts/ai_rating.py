#!/usr/bin/env python3
"""
AI 评分助手 - 对 S 级和 A 级公司进行 AI 评分并写入 tracker.db
使用规则：
1. 读取 profile.md 画像
2. 查询待评分公司
3. 关键词预筛
4. 批量 LLM 评分（每 5 家一批）
5. 更新数据库
"""

import sqlite3
import json
import os
import sys
import re
import time
import urllib.request
import urllib.error

# 配置
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'tracker.db')
PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'profile.md')
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

API_BASE = "http://localhost:20128/v1"
MODEL = "Hermes"

def load_env():
    """从 .env 文件读取 API key"""
    api_key = None
    try:
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ANTHROPIC_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                elif line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                elif line.startswith('LLM_API_KEY='):
                    api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return api_key or "sk-placeholder"

def load_profile():
    """读取画像文件"""
    with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def get_companies(db):
    """获取待评分公司"""
    cur = db.cursor()
    cur.execute("""
        SELECT id, name, industry, job_type, city, priority, match_reason, tags 
        FROM companies 
        WHERE priority IN ('S','A') AND score IS NULL 
        ORDER BY priority, id
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in rows]

def keyword_filter(company):
    """关键词预筛：如果匹配到淘汰关键词，返回 True（应淘汰）"""
    text = f"{company.get('match_reason', '') or ''} {company.get('job_type', '') or ''} {company.get('name', '') or ''} {company.get('industry', '') or ''}"
    text_lower = text.lower()
    
    keywords = ['实习', '管培', '销售', '客服', '法务', '行政', '财务', 'hr', '大数据', '法律', '前台']
    
    for kw in keywords:
        if kw in text_lower:
            company['_eliminated'] = True
            company['_score'] = 0
            company['_reason'] = f'预筛淘汰: {kw}'
            return True
    
    company['_eliminated'] = False
    return False

def call_llm(prompt, api_key, max_retries=3):
    """调用 9Router LLM API"""
    url = f"{API_BASE}/chat/completions"
    
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个专业的 AI 评分助手，根据用户画像和公司信息，对岗位匹配度进行评分。请严格按照 JSON 格式输出。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"}
    }).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result['choices'][0]['message']['content']
                content = content.strip()
                
                # 尝试用正则匹配包含在 [ ... ] 之间的 JSON 数组内容
                match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
                
                # 尝试直接解析
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # 尝试提取第一个 [ 到最后一个 ]
                    start = content.find('[')
                    end = content.rfind(']')
                    if start >= 0 and end > start:
                        try:
                            return json.loads(content[start:end+1])
                        except json.JSONDecodeError:
                            pass
                    raise
        except urllib.error.HTTPError as e:
            print(f"  HTTP Error {e.code}: {e.reason}")
            if e.code == 401:
                print("  API 认证失败，请检查 API key")
                return None
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  等待 {wait}s 后重试...")
                time.sleep(wait)
        except (json.JSONDecodeError, KeyError, urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f"  API 调用错误: {e}")
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  等待 {wait}s 后重试...")
                time.sleep(wait)
    
    return None

def build_batch_prompt(profile, companies_batch):
    """构造一批公司的评分 Prompt"""
    companies_json = []
    for c in companies_batch:
        companies_json.append({
            "id": c['id'],
            "name": c['name'],
            "industry": c['industry'],
            "job_type": c['job_type'],
            "city": c['city'],
            "priority": c['priority'],
            "match_reason": c.get('match_reason', ''),
            "tags": c.get('tags', '')
        })
    
    prompt = f"""# 用户画像
{profile}

# 评分规则
请根据用户画像与以下公司的匹配程度，对每家公司进行评分（0-100分）。

评分维度：
- 行业匹配度 (0-30分)：公司行业与用户目标行业（3D打印/增材制造、工业自动化、机器人、智能装备）的匹配程度
- 岗位匹配度 (0-40分)：岗位与用户目标岗位（嵌入式工程师、3D打印研发、机器人/自动化控制）的匹配程度
- 城市匹配度 (0-15分)：城市与用户偏好城市（深圳、上海、大连、北京、广州、杭州）的匹配程度
- 技术匹配度 (0-15分)：公司技术方向与用户技术栈（嵌入式、控制算法、3D打印、仿真等）的匹配程度

注意：
- 评分 0 分表示完全不匹配
- 评分 60+ 表示值得考虑
- 评分 80+ 表示高度匹配

# 待评分公司列表
{json.dumps(companies_json, ensure_ascii=False, indent=2)}

请输出 JSON 数组，格式如下：
[{{"id": 1, "score": 85, "reason": "匹配理由（简述行业+岗位+城市+技术匹配度）", "missing": "缺失项（如：需要xx经验，不满足写无）"}}]
"""
    return prompt

def update_scores(db, results):
    """更新评分到数据库"""
    cur = db.cursor()
    updated = 0
    for r in results:
        if 'id' in r and 'score' in r:
            score = r['score']
            # 确保分数在 0-100 范围
            score = max(0, min(100, int(score)))
            reason = r.get('reason', '')
            missing = r.get('missing', '')
            full_reason = reason
            if missing:
                full_reason += f" | 缺失: {missing}"
            
            cur.execute(
                "UPDATE companies SET score=?, score_reason=? WHERE id=? AND score IS NULL",
                (score, full_reason, r['id'])
            )
            if cur.rowcount > 0:
                updated += 1
    db.commit()
    return updated

def main():
    api_key = load_env()
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    
    profile = load_profile()
    print(f"已加载画像: {len(profile)} 字符")
    
    db = sqlite3.connect(DB_PATH)
    
    companies = get_companies(db)
    print(f"待评分公司总数: {len(companies)}")
    
    # 统计
    eliminated = 0
    to_score = []
    
    for c in companies:
        if keyword_filter(c):
            eliminated += 1
        else:
            to_score.append(c)
    
    print(f"预筛淘汰: {eliminated}")
    print(f"需要 LLM 评分: {len(to_score)}")
    
    # 先写入淘汰的
    cur = db.cursor()
    for c in companies:
        if c.get('_eliminated'):
            cur.execute(
                "UPDATE companies SET score=?, score_reason=? WHERE id=? AND score IS NULL",
                (c['_score'], c['_reason'], c['id'])
            )
    db.commit()
    print(f"已写入淘汰记录: {eliminated}")
    
    # 批量 LLM 评分
    batch_size = 5
    total_updated = 0
    total_batches = (len(to_score) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(to_score))
        batch = to_score[start:end]
        
        batch_ids = [c['id'] for c in batch]
        print(f"\n--- 批次 {batch_idx + 1}/{total_batches} (公司 ID: {batch_ids}) ---", flush=True)
        
        prompt = build_batch_prompt(profile, batch)
        print(f"  Prompt 长度: {len(prompt)} 字符", flush=True)
        
        result = call_llm(prompt, api_key)
        
        if result is None:
            print(f"  ⚠️ 批次 {batch_idx + 1} API 调用失败，跳过此批", flush=True)
            continue
        
        # 解析结果
        if isinstance(result, dict) and 'results' in result:
            results_list = result['results']
        elif isinstance(result, dict) and 'companies' in result:
            results_list = result['companies']
        elif isinstance(result, list):
            results_list = result
        else:
            print(f"  ⚠️ 无法解析结果格式: {type(result)}", flush=True)
            print(f"  原始结果: {json.dumps(result, ensure_ascii=False)[:200]}", flush=True)
            continue
        
        # 确保每个结果都有 id
        parsed = []
        for item in results_list:
            if isinstance(item, dict):
                parsed.append(item)
        
        print(f"  解析到 {len(parsed)} 个评分结果", flush=True)
        for p in parsed:
            print(f"    ID {p.get('id', '?')}: score={p.get('score', '?')}, reason={p.get('reason', '')[:40]}...", flush=True)
        
        n = update_scores(db, parsed)
        total_updated += n
        print(f"  本批更新: {n} 条", flush=True)
        
        # 批次间稍作延迟
        if batch_idx < total_batches - 1:
            time.sleep(1)
    
    # 最终统计
    cur.execute("SELECT COUNT(*) FROM companies WHERE priority IN ('S','A') AND score IS NOT NULL")
    scored = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM companies WHERE priority IN ('S','A') AND score = 0")
    zero_score = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM companies WHERE priority IN ('S','A') AND score IS NULL")
    still_null = cur.fetchone()[0]
    cur.execute("SELECT id, name, score, score_reason FROM companies WHERE priority IN ('S','A') AND score IS NOT NULL AND score > 0 ORDER BY score DESC LIMIT 5")
    top5 = cur.fetchall()
    
    print(f"\n{'='*60}")
    print(f"评分完成统计:")
    print(f"  已评分: {scored}")
    print(f"  淘汰(0分): {zero_score}")
    print(f"  未评分(NULL): {still_null}")
    print(f"  最高评分 Top 5:")
    for t in top5:
        print(f"    ID={t[0]} {t[1]}: {t[2]}分 - {t[3][:60] if t[3] else ''}")
    
    db.close()

if __name__ == '__main__':
    main()