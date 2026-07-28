#!/usr/bin/env python3
"""
每日新公司/岗位发现脚本。
自动搜索目标行业的公司，检查与已有公司的重复，然后写入 DB。
"""
import sqlite3
import os
import json
import re
import sys

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tracker.db')

# 我们重点关注的方向（每天轮换一个，避免重复）
FOCUS_AREAS = [
    # (行业, 搜索关键词, 岗位方向)
    ('3D打印', '3D打印 公司 招聘 自动化工程师', '自动化工程师/控制算法'),
    ('3D打印', '增材制造 设备研发 招聘', '设备研发/嵌入式'),
    ('机器人', '机器人公司 运动控制 招聘 2026', '运动控制工程师'),
    ('机器人', '协作机器人 伺服驱动 招聘', '伺服/驱动工程师'),
    ('工业自动化', '工业自动化 PLC 嵌入式 招聘', 'PLC/嵌入式工程师'),
    ('工业自动化', '自动化设备 控制算法 招聘', '控制算法工程师'),
    ('高端装备', '高端装备 激光 数控 招聘', '数控/激光工程师'),
    ('汽车制造', '新能源汽车 电机控制 热管理 招聘', '电机控制/热管理'),
    ('半导体', '半导体设备 工艺控制 招聘', '半导体设备工程师'),
    ('半导体', '晶圆制造 自动化 招聘', '半导体自动化工程师'),
    ('能源与新能源', '储能 逆变器 控制 招聘 2026', '电力电子/控制工程师'),
    ('医疗器械', '医疗器械 嵌入式 控制 招聘', '医疗设备嵌入式'),
    ('医疗器械', '医疗机器人 机电 招聘', '医疗机器人工程师'),
    ('航空航天', '航天 飞控 机电 招聘 2026', '飞控/机电工程师'),
    ('人工智能/算法', 'AI算法 机器人 控制 招聘 2026', 'AI算法/控制'),
]

def get_existing_names(cursor):
    """获取所有已存在的公司名，用于去重"""
    cursor.execute("SELECT name FROM companies")
    return set(r[0] for r in cursor.fetchall())

def get_existing_urls(cursor):
    """获取所有已存在的 URL"""
    cursor.execute("SELECT url FROM applications WHERE url IS NOT NULL")
    return set(r[0] for r in cursor.fetchall())

def normalize(name):
    """简单标准化，用于模糊匹配"""
    name = re.sub(r'[（(].*?[）)]', '', name)
    name = name.replace('（中国）', '').replace('（中国）有限公司', '')
    name = name.replace('有限公司', '').replace('股份', '').replace('集团', '').replace('科技', '')
    name = name.replace('（', '').replace('）', '').strip()
    # 处理英文名
    if '/' in name:
        name = name.split('/')[0]
    return name.strip()

def is_duplicate(new_name, existing_names):
    """检查是否重复：精确匹配 + 模糊匹配"""
    norm_new = normalize(new_name)
    if not norm_new or len(norm_new) < 2:
        return True  # 太短就跳过
    for en in existing_names:
        norm_existing = normalize(en)
        if norm_new in norm_existing or norm_existing in norm_new:
            return True
        # 关键子串匹配
        for kw in [norm_new[:4], norm_new[2:6]]:
            if len(kw) >= 3 and kw in norm_existing:
                return True
    return False

def get_background_info():
    """返回用户的背景信息，用于LLM评估匹配度"""
    return """
用户背景：机械工程硕士
研究方向：高温FDM 3D打印控制系统（大尺寸腔体温控）
核心技能：Klipper固件、PID/MPC温控算法、力传感器集成、雷赛CL57C闭环
目标岗位：自动化工程师/机电工程师(热控/系统调试方向)
目标城市：深圳、杭州、上海、北京
"""

def analyze_match(name, industry, url, job_type):
    """生成匹配理由"""
    reasons = []
    # 基于行业的关键词匹配
    if '3D' in industry or '打印' in industry:
        reasons.append('热控/嵌入式经验高度匹配')
    elif '机器人' in industry:
        reasons.append('运动控制/嵌入式技能匹配')
    elif '自动化' in industry:
        reasons.append('自动化控制专业对口')
    elif '半导体' in industry:
        reasons.append('半导体设备自动化方向')
    elif '汽车' in industry:
        reasons.append('汽车电子/热管理方向')
    elif '航天' in industry or '航空' in industry:
        reasons.append('军工/航空航天控制方向')
    elif '能源' in industry:
        reasons.append('能源控制/电力电子方向')
    elif '医疗' in industry:
        reasons.append('精密仪器/嵌入式方向')
    elif '半导体' in industry:
        reasons.append('半导体设备自动化方向')
    else:
        reasons.append('自动化/机电方向对口')
    if '算法' in job_type or '控制' in job_type:
        reasons.append('算法/控制经验')
    if '嵌入' in job_type:
        reasons.append('嵌入式开发')
    return '；'.join(reasons[:3])


def main():
    print("=== 每日新公司发现脚本 ===")
    print(f"时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    existing_names = get_existing_names(c)
    print(f"当前公司总数: {len(existing_names)}")
    
    # 从focus_areas选一个今天重点扫的方向
    today_idx = __import__('datetime').date.today().day % len(FOCUS_AREAS)
    focus = FOCUS_AREAS[today_idx]
    print(f"今日重点: {focus[0]} - {focus[1]}")
    
    # 这里使用 web_search 列出目标
    from hermes_tools import web_search
    
    all_results = []
    searched_keywords = set()
    
    # 搜索3个关键词
    keywords = [
        f"{focus[1]}",
        f"{focus[0]} 自动化 机电 2026 招聘 校招",
        f"{focus[0]} 控制 嵌入式 工程师 招聘 2027"
    ]
    
    for kw in keywords:
        if kw in searched_keywords:
            continue
        searched_keywords.add(kw)
        try:
            r = web_search(kw, limit=10)
            if r and 'data' in r and 'web' in r['data']:
                for item in r['data']['web']:
                    title = item.get('title','')
                    url = item.get('url','')
                    desc = item.get('description','')
                    if any(kw in title+desc for kw in ['招聘','校招','自动化','工程师','机电']):
                        all_results.append({'title': title, 'url': url, 'desc': desc, 'keyword': kw})
        except Exception as e:
            print(f"  搜索 '{kw}' 失败: {e}")
            continue
    
    # 去重
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r['url'] not in seen_urls:
            seen_urls.add(r['url'])
            unique_results.append(r)
    
    print(f"搜索到 {len(unique_results)} 条潜在结果")
    
    # 提取公司名并去重
    added_count = 0
    for r in unique_results[:20]:  # 最多处理20条
        title = r['title']
        url = r['url']
        desc = r['desc']
        
        # 从标题/描述中提取公司名（启发式）
        # 常见模式：公司名+招聘/招...
        company_candidates = set()
        
        # 尝试从title提取
        parts = re.split(r'[（(]', title)
        for p in parts:
            p = p.strip()
            # 找公司名：通常是2-6个字
            # 匹配类似 "汇川技术2027校招" 或 "深圳拓竹科技" 或 "大疆创新"
            matches = re.findall(r'([\u4e00-\u9fa5]{2,8})(?:202[67]|招|聘|校|社|秋|春)', p)
            for m in matches:
                company_candidates.add(m)
            # 从描述抓
            desc_matches = re.findall(r'([\u4e00-\u9fa5]{2,8})(?:科技|集团|有限|股份|公司)', desc)
            for m in desc_matches:
                company_candidates.add(m + '科技' if not m.endswith(('科技','集团','有限','股份')) else m)
        
        for company_name in company_candidates:
            if not company_name or len(company_name) < 3:
                continue
            if is_duplicate(company_name, existing_names):
                continue
            
            # 推断行业
            industry = focus[0]
            for ind_kw, ind_name in [
                ('3D','3D打印'),('打印','3D打印'),('增材','3D打印'),
                ('机器','机器人'),('机器人','机器人'),
                ('新能源','能源与新能源'),('光伏','能源与新能源'),('风电','能源与新能源'),('储能','能源与新能源'),('能源','能源与新能源'),
                ('汽车','汽车制造'),('整车','汽车制造'),
                ('半导体','半导体'),('芯片','半导体'),('集成电路','半导体'),
                ('激光','高端装备'),('数控','高端装备'),
                ('医疗','医疗器械'),('药','医疗器械'),
                ('航天','航空航天'),('航空','航空航天'),('军工','航空航天'),('兵器','航空航天'),
                ('自动化','工业自动化'),('工控','工业自动化'),
                ('无人','机器人'),
                ('智能','机器人'),
            ]:
                if ind_kw in company_name:
                    industry = ind_name
                    break
            
            # 推断岗位方向
            job_type = focus[2] if focus[0] == industry else '自动化/机电工程师'
            if '算法' in desc:
                job_type = '控制算法工程师'
            elif '嵌入' in desc:
                job_type = '嵌入式工程师'
            elif '电机' in desc or '伺服' in desc:
                job_type = '电机控制工程师'
            elif '热' in desc:
                job_type = '热管理/热控工程师'
            
            match_reason = analyze_match(company_name, industry, url, job_type)
            
            # 从URL提取官网
            website = url
            if 'zhipin' in url or 'liepin' in url or 'maimai' in url:
                website_search = re.search(r'https?://[^/]+', url)
                website = website_search.group(0) if website_search else ''
            
            # 写入DB
            try:
                c.execute("""INSERT OR IGNORE INTO companies 
                    (name, industry, city, job_type, match_reason, priority, website, salary_min, salary_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (company_name, industry, '', job_type, match_reason, 'B', website, None, None))
                if c.rowcount > 0:
                    conn.commit()
                    existing_names.add(company_name)
                    added_count += 1
                    print(f"  ✅ 新增: {company_name} | {industry} | {job_type}")
            except Exception as e:
                print(f"  ❌ 写入失败 {company_name}: {e}")
    
    print(f"\n=== 完成：本次新增 {added_count} 家公司 ===")
    conn.close()

if __name__ == '__main__':
    main()
