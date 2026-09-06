"""
scripts/fix_db_locations.py
全量岗位数据库工作地点校对与清洗脚本。
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

COMMON_CITIES = [
    "北京", "上海", "深圳", "广州", "杭州", "南京", "苏州", "成都", "武汉", "西安",
    "重庆", "天津", "长沙", "合肥", "厦门", "无锡", "青岛", "大连", "济南", "沈阳",
    "宁波", "郑州", "福州", "东莞", "佛山", "常州", "珠海", "昆明", "南昌", "贵阳",
    "哈尔滨", "长春", "石家庄", "南宁", "海口", "太原", "兰州", "银川", "西宁", "乌鲁木齐",
    "拉萨", "呼和浩特", "香港", "澳门", "台湾", "芜湖", "温州", "烟台", "洛阳", "柳州",
    "宁德", "廊坊", "绍兴", "桂林", "中山", "宜昌", "株洲", "绵阳", "淄博", "威海",
    "嘉兴", "湖州", "金华", "台州", "保定", "邯郸", "唐山", "徐州", "南通", "扬州",
    "镇江", "泰州", "盐城", "淮安", "宿迁", "连云港", "赣州", "九江", "上饶", "宜春",
    "吉安", "抚州", "景德镇", "萍乡", "新余", "鹰潭", "漳州", "泉州", "莆田", "三明",
    "南平", "龙岩", "宁德", "衡阳", "岳阳", "常德", "益阳", "郴州", "永州", "怀化",
    "娄底", "湘潭", "襄阳", "荆州", "黄冈", "孝感", "荆门", "十堰", "黄石", "咸宁",
    "随州", "鄂州", "恩施", "仙桃", "天门", "潜江", "神农架", "全国各省市", "全国", "远程"
]

def clean_location(raw_loc: str) -> str:
    """清洗异常长文本或格式错乱的地点"""
    if not raw_loc:
        return "全国"
    s = raw_loc.strip()
    s = re.sub(r'^[【\[\(（]?工作地点[】\]\)）]?\s*[:：]?', '', s)
    s = re.sub(r'^[【\[\(（]?工作城市[】\]\)）]?\s*[:：]?', '', s)
    s = re.sub(r'^[【\[\(（]?地点[】\]\)）]?\s*[:：]?', '', s)
    s = s.strip(" \t\r\n,、;；/|")

    if any(kw in s for kw in ["学历", "统招", "专业", "院校", "毕业生", "招聘"]):
        return "全国"

    # 若为长街道/园区地址，提取前置城市名
    if len(s) > 8:
        for c in COMMON_CITIES:
            if s.startswith(c) and c not in ["全国", "远程", "海外"]:
                return c
    return s

def extract_cities_from_text(text: str) -> list[str]:
    """从文本中按出现顺序提取已知城市"""
    if not text:
        return []
    found = []
    # 按照在文本中出现的位置排序
    matches = []
    for city in COMMON_CITIES:
        idx = text.find(city)
        if idx != -1:
            matches.append((idx, city))
    matches.sort(key=lambda x: x[0])
    for _, city in matches:
        if city not in found:
            found.append(city)
    return found

def fix_all_locations(db_path: str, dry_run: bool = False, wcv_cache_path: str = "wcv_cards_cache.json"):
    WONDERCV_TAGS_MAP = {}
    if os.path.exists(wcv_cache_path):
        try:
            with open(wcv_cache_path, "r", encoding="utf-8") as f:
                WONDERCV_TAGS_MAP = json.load(f)
            print(f"[*] Loaded {len(WONDERCV_TAGS_MAP)} WonderCV card tags from {wcv_cache_path}")
        except Exception as e:
            print(f"[!] Warning: failed to load {wcv_cache_path}: {e}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, company, location, type_tags, description, source_site, detail_url FROM jobs")
    rows = cursor.fetchall()
    print(f"[*] Total jobs in database: {len(rows)}")

    updates = []
    overseas_fixed_count = 0
    clean_fixed_count = 0

    for row in rows:
        jid, title, comp, loc, type_tags_str, desc, source, detail_url = row
        loc = loc or ""
        desc = desc or ""
        type_tags = []
        try:
            type_tags = json.loads(type_tags_str) if type_tags_str else []
        except Exception:
            type_tags = []

        new_loc = loc
        tags_modified = False

        # 规则 1：求职方舟多地点提取修正
        if source == "求职方舟":
            # 查找 【工作城市】:
            desc_cities = []
            for line in desc.split("\n"):
                if "【工作城市】:" in line:
                    city_part = line.split("【工作城市】:")[1].strip()
                    desc_cities = [c.strip() for c in re.split(r'[,、;；/| ]+', city_part) if c.strip()]
                    break

            if desc_cities:
                domestic = [c for c in desc_cities if c not in ["海外", "境外", "全国", "远程"]]
                # 检查当前 loc 是否为海外且存在国内城市，或者包含海外
                if loc in ["海外", "境外"] and domestic:
                    new_loc = "、".join(desc_cities[:3]) if len(desc_cities) <= 3 else "、".join(domestic[:3])
                    overseas_fixed_count += 1
                    if "海外" not in type_tags:
                        type_tags.append("含海外")
                        tags_modified = True
                elif loc in ["海外", "境外"] and not domestic:
                    # 纯海外公司（如中建阿尔及利亚公司、OMP中国海外基地）保留海外
                    pass

        # 规则 2：WonderCV 误判海外修正
        elif source == "wondercv":
            if loc in ["海外", "境外"]:
                # 优先从卡片缓存中读取真实地点标签
                live_tags = []
                if detail_url:
                    path = "/" + detail_url.split("wondercv.com/")[1] if "wondercv.com/" in detail_url else detail_url
                    if path in WONDERCV_TAGS_MAP:
                        live_tags = WONDERCV_TAGS_MAP[path]
                
                # 从 live_tags 中识别国内城市
                domestic_from_tags = []
                for t in live_tags:
                    for c in COMMON_CITIES:
                        if c in t and c not in ["海外", "境外", "全国", "远程", "全国各省市"]:
                            if c not in domestic_from_tags:
                                domestic_from_tags.append(c)
                
                if domestic_from_tags:
                    new_loc = "、".join(domestic_from_tags[:3])
                    overseas_fixed_count += 1
                    if "含海外" not in type_tags:
                        type_tags.append("含海外")
                        tags_modified = True
                else:
                    # 从标题与描述中探测真实城市
                    found_cities = extract_cities_from_text(f"{title} {desc}")
                    domestic = [c for c in found_cities if c not in ["海外", "境外", "全国", "远程", "全国各省市"]]
                    if domestic:
                        new_loc = domestic[0]
                        overseas_fixed_count += 1
                        if "含海外" not in type_tags:
                            type_tags.append("含海外")
                            tags_modified = True

        # 规则 3：清洗异常格式、超长文本、前缀/后缀脏字符
        cleaned = clean_location(new_loc)
        if cleaned != new_loc:
            clean_fixed_count += 1
            new_loc = cleaned

        if new_loc != loc or tags_modified:
            new_tags_str = json.dumps(type_tags, ensure_ascii=False) if tags_modified else type_tags_str
            updates.append((new_loc, new_tags_str, jid, loc, comp, title, new_loc))

    print(f"[*] Detected {len(updates)} jobs needing correction.")
    print(f"    - Overseas misclassification fixed: {overseas_fixed_count}")
    print(f"    - Location format cleaned: {clean_fixed_count}")

    print("\n[+] Top 15 Sample Updates:")
    for u in updates[:15]:
        print(f"  [{u[4]}] (id: {u[2][:25]}...)")
        print(f"    OLD: '{u[3]}' -> NEW: '{u[0]}'")

    if dry_run:
        print("\n[!] Dry run mode: NO changes were written to database.")
    else:
        print("\n[*] Applying changes to database...")
        for u in updates:
            new_loc, new_tags_str, jid = u[0], u[1], u[2]
            cursor.execute("UPDATE jobs SET location = ?, type_tags = ? WHERE id = ?", (new_loc, new_tags_str, jid))
            # 同步更新 FTS 索引
            cursor.execute("UPDATE jobs_fts SET location = ? WHERE rowid = (SELECT rowid FROM jobs WHERE id = ?)", (new_loc, jid))
        conn.commit()
        print(f"[OK] Successfully updated {len(updates)} jobs and their FTS index.")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix job locations in public_jobs.db")
    parser.add_argument("--db", default="data/public_jobs.db", help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without modifying DB")
    args = parser.parse_args()

    fix_all_locations(args.db, args.dry_run)



