import asyncio
import sys
import datetime
import re
import httpx
from typing import List
from src.models import JobItem
from src.services.spiders.base_spider import BaseJobSpider, sanitize_date_str

def normalize_education_str(edu_str: str) -> str:
    """归一化文本为标准学历枚举"""
    if not edu_str:
        return "不限"
    s = str(edu_str)
    if "博士" in s:
        return "博士"
    if "硕" in s or "研究生" in s:
        return "硕士"
    if "本" in s:
        return "本科"
    if "专" in s:
        return "大专"
    return "不限"

class QiuzhiFangzhouSpider(BaseJobSpider):
    """
    求职方舟 (qiuzhifangzhou.com) 真实校招/秋招网申数据爬虫适配器
    """
    API_URL = "https://api.qiuzhifangzhou.com/api/campus/getCampusList"
    HEADERS = {
        "Origin": "https://www.qiuzhifangzhou.com",
        "Referer": "https://www.qiuzhifangzhou.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self, days_back: int = 15):
        self.days_back = days_back

    async def fetch_jobs(self, since_date: str = None) -> List[JobItem]:
        today = datetime.date.today()
        if since_date:
            try:
                target_date = datetime.datetime.strptime(since_date, "%Y-%m-%d").date()
            except Exception:
                target_date = today - datetime.timedelta(days=self.days_back)
        else:
            target_date = today - datetime.timedelta(days=self.days_back)

        # 构造日期范围
        date_list = []
        curr = today
        while curr >= target_date:
            date_list.append({"date": curr.strftime("%Y-%m-%d"), "md5": ""})
            curr -= datetime.timedelta(days=1)

        if not date_list:
            date_list.append({"date": today.strftime("%Y-%m-%d"), "md5": ""})

        jobs: List[JobItem] = []
        # 按每批 10 天请求，包含重试退避机制
        chunk_size = 10
        async with httpx.AsyncClient(headers=self.HEADERS, timeout=httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=10.0)) as client:
            for i in range(0, len(date_list), chunk_size):
                chunk = date_list[i:i + chunk_size]
                res_json = None
                
                # 重试最多2次
                for attempt in range(2):
                    try:
                        resp = await client.post(self.API_URL, json={"dateList": chunk})
                        if resp.status_code == 200:
                            res_json = resp.json()
                            break
                    except Exception as e:
                        if attempt == 0:
                            await asyncio.sleep(1.0)
                        else:
                            print(f"[FangzhouSpider] Network error after retry on chunk {chunk[:2]}...: {e}")
                
                if not res_json:
                    continue

                campus_list = res_json.get("campusList", [])
                for day_item in campus_list:
                    pub_date = sanitize_date_str(day_item.get("date"))
                    for item in day_item.get("datas", []):
                        company = item.get("company") or "未知企业"
                        positions_str = item.get("positions") or "校招岗位"
                        raw_base_id = f"fangzhou-{item.get('id')}"
                        
                        locations = item.get("locations") or "全国"
                        raw_industry = item.get("industry") or "互联网/技术"
                        type_tags = list(item.get("typeTag") or [])
                        batch = item.get("batch")
                        if batch and batch not in type_tags:
                            type_tags.append(batch)
                        
                        # 策略优化3：分离企业性质与行业分类
                        nature_keywords = ["民企", "上市公司", "央企", "国企", "外企", "民营企业"]
                        if any(k == raw_industry for k in nature_keywords):
                            if raw_industry not in type_tags:
                                type_tags.append(raw_industry)
                            industry = "其他/综合"
                        else:
                            industry = raw_industry

                        raw_apply_url = item.get("applyUrl") or item.get("sourceUrl") or ""
                        # 策略优化4：过滤非法协议（如 chrome-error://）
                        if raw_apply_url.startswith(("http://", "https://")):
                            apply_url = raw_apply_url
                        else:
                            apply_url = ""

                        raw_deadline = item.get("deadline")
                        # 策略优化5：规范截止时间格式
                        if raw_deadline and re.match(r'^\d{4}-\d{2}-\d{2}$', str(raw_deadline).strip()):
                            deadline = str(raw_deadline).strip()
                        else:
                            deadline = None
                            if raw_deadline and "招满" in str(raw_deadline) and "招满即止" not in type_tags:
                                type_tags.append("招满即止")

                        # 拆分岗位列表，实现“一岗一条”
                        raw_positions = re.split(r'[\r\n、/；;，,]+', positions_str)
                        cleaned_positions = []
                        for p in raw_positions:
                            p = re.sub(r'^[0-9一二三四五六七八九十]+[、.\s]+', '', p.strip())
                            p = re.sub(r'\s*\([^)]*\)$', '', p)
                            p = re.sub(r'\s*（[^）]*）$', '', p)
                            p = p.strip()
                            if p and len(p) <= 40 and not any(p.startswith(x) for x in ['......', '...', '等', '类']):
                                if p not in cleaned_positions:
                                    cleaned_positions.append(p)

                        if not cleaned_positions:
                            cleaned_positions = [positions_str[:35]]

                        # 针对多城市，优先选用国内主要地级市/省会，避免“海外”等排在首位误覆盖国内主力岗位
                        primary_location = locations
                        if "、" in locations:
                            city_candidates = [c.strip() for c in locations.split("、") if c.strip()]
                            domestic_cities = [c for c in city_candidates if c not in ["海外", "境外"]]
                            primary_location = domestic_cities[0] if domestic_cities else city_candidates[0]

                        for pos in cleaned_positions:
                            clean_tag = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '', pos)[:20]
                            single_id = f"{raw_base_id}-{clean_tag}" if len(cleaned_positions) > 1 else raw_base_id
                            desc = (
                                f"【招聘企业】: {company}\n"
                                f"【招聘职位】: {pos}\n"
                                f"【招聘批次】: {batch or '秋招/校招'}\n"
                                f"【工作城市】: {locations}\n"
                                f"【所属行业】: {industry}\n"
                                f"【截止时间】: {deadline or '招满即止'}\n"
                                f"【网申直达链接】: {apply_url}\n"
                                f"【同批次其他岗位】: {positions_str}"
                            )

                            job = JobItem(
                                id=single_id,
                                title=f"{company} - {pos}",
                                company=company,
                                location=primary_location,
                                industry=industry,
                                batch=batch,
                                deadline=deadline,
                                salary_range="面议 / 校招标准",
                                publish_date=pub_date,
                                description=desc,
                                source_site="求职方舟",
                                detail_url=apply_url,
                                popular_level=int(item.get("popular") or 1),
                                type_tags=list(type_tags)
                            )
                            jobs.append(job)
        return jobs


FangzhouJobSpider = QiuzhiFangzhouSpider

