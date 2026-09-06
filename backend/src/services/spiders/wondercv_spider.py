"""WonderCV (超级简历) Spider implementation for fetching and parsing campus recruitment postings.
Extracts structured company, batch, title, location, education requirement, deadline, and direct application links.
"""
import re
import httpx
import logging
import hashlib
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from src.models import JobItem
from src.repositories.job_repository import JobRepository
from src.services.spiders.base_spider import BaseJobSpider

logger = logging.getLogger(__name__)

class WondercvSpider(BaseJobSpider):
    BASE_URL = "https://www.wondercv.com"
    LIST_URL = "https://www.wondercv.com/xiaozhao"
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.wondercv.com/xiaozhao"
    }

    def __init__(self, repo: Optional[JobRepository] = None):
        self.repo = repo or JobRepository()

    def generate_job_id(self, company: str, title: str, location: str, raw_id: Optional[str] = None) -> str:
        """Generate deterministic stable identifier for WonderCV jobs."""
        if raw_id:
            cleaned_id = str(raw_id).strip().replace("/", "_")
            if cleaned_id.startswith("wcv_"):
                return cleaned_id
            return f"wcv_{cleaned_id}"
        unique_str = f"wondercv_{company.strip()}_{title.strip()}_{location.strip()}"
        return f"wcv_{hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12]}"

    def parse_html_page(self, html_content: str) -> List[JobItem]:
        """Parse one page of WonderCV campus listings into JobItem models."""
        soup = BeautifulSoup(html_content, "html.parser")
        jobs: List[JobItem] = []

        # Each listing card: primary structure is section.jobs-grid > a.campus-job-card
        cards = soup.select("section.jobs-grid > a, a.campus-job-card, .campus-job-card, .job-item, div[class*='job-item']")

        for card in cards:
            title_elem = card.select_one(".job-name, .summary, h2, h3, .title")
            company_elem = card.select_one(".company, .company-name, .name")
            
            if not company_elem:
                continue

            company = company_elem.get_text(strip=True)
            raw_title = title_elem.get_text(strip=True) if title_elem else f"{company}校园招聘"
            
            # 策略优化1：防止首句新闻导语直接污染岗位title
            # 若原始标题过长或包含标点，截取第一个完整句子作为主标题
            title_parts = re.split(r'[，。！？\r\n]', raw_title)
            short_title = title_parts[0].strip() if title_parts and title_parts[0].strip() else raw_title
            if len(short_title) > 40:
                short_title = short_title[:37] + "..."
            full_title = short_title

            # Location / education / nature tags
            tags_elem = card.select(".info-tag, .tag, .info-tags span, .job-info span, .tags span, .job-tag")
            tags = [t.get_text(strip=True) for t in tags_elem if t.get_text(strip=True)]
            
            location = "全国"
            education_req = "不限"
            industry = "综合"
            
            # Standard city detection list
            major_cities = [
                "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安", "合肥", "苏州", "大连",
                "重庆", "天津", "长沙", "青岛", "厦门", "宁波", "郑州", "无锡", "福州", "济南", "沈阳", "长春",
                "哈尔滨", "石家庄", "南昌", "昆明", "贵阳", "南宁", "海口", "兰州", "银川", "西宁", "乌鲁木齐",
                "全国", "远程", "海外"
            ]

            detected_cities = []
            enterprise_nature = []
            for t in tags:
                if any(city_kw in t for city_kw in major_cities):
                    detected_cities.append(t)
                elif any(edu_kw in t for edu_kw in ["本科", "硕士", "博士", "大专"]):
                    if "博士" in t:
                        education_req = "博士"
                    elif "硕" in t or "研究生" in t:
                        education_req = "硕士"
                    elif "本" in t:
                        education_req = "本科"
                    elif "专" in t:
                        education_req = "大专"
                    else:
                        education_req = t
                elif any(nat_kw in t for nat_kw in ["国企", "央企", "外企", "民企", "上市公司", "民营企业"]):
                    enterprise_nature.append(t)

            if detected_cities:
                # 优先选用国内具体城市，避免“海外”排在最后冲刷覆盖掉前面的国内主要城市
                domestic_cities = [c for c in detected_cities if c not in ["海外", "境外"]]
                target_cities = domestic_cities if domestic_cities else detected_cities
                # 如果有多个地点，用逗号连接保留
                location = "、".join(target_cities[:3])

            # Direct link & unique slug (card itself might be <a>)
            href = card.get("href") if card.name == "a" else None
            if not href:
                link_elem = card.select_one("a[href*='/xiaozhao/']")
                if link_elem:
                    href = link_elem.get("href")

            detail_url = ""
            raw_id = None
            if href:
                candidate_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                # 策略优化4：校验 URL 协议安全性，拒绝非法协议入库
                if candidate_url.startswith(("http://", "https://")):
                    detail_url = candidate_url
                
                # Extract slug e.g. /xiaozhao/ceri-2027-campus-recruitment-14155-53c215/ -> 14155-53c215
                slug_match = re.search(r'/xiaozhao/([^/]+)/?', href)
                if slug_match:
                    raw_id = slug_match.group(1)

            # Recruit category / majors
            cat_elem = card.select_one(".job-category, .position-type, .positions")
            category_text = cat_elem.get_text(strip=True) if cat_elem else ""

            # Extract target graduate year e.g. 2026/2027
            year_matches = re.findall(r'202[4-9]', full_title + " " + category_text)
            target_grad_year = sorted(list(set(year_matches)))

            # Batch recognition (秋招, 春招, 补录, 实习)
            batch = "校园招聘"
            if "秋招" in full_title or "秋季" in full_title:
                batch = "秋招"
            elif "春招" in full_title or "春季" in full_title:
                batch = "春招"
            elif "补录" in full_title:
                batch = "补录"
            elif "实习" in full_title:
                batch = "实习"

            job_id = self.generate_job_id(company, full_title, location, raw_id)

            type_tags = [batch]
            if enterprise_nature:
                type_tags.extend(enterprise_nature)
            if industry and industry != "综合":
                type_tags.append(industry)
            if category_text:
                type_tags.append(category_text[:20])

            # Parse date e.g. "收录 2026.09.04" -> "2026-09-04"
            date_elem = card.select_one(".card-date, .date, span[class*='date']")
            raw_date = date_elem.get_text(strip=True) if date_elem else ""
            pub_date = ""
            date_match = re.search(r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', raw_date)
            if date_match:
                y, m, d = date_match.groups()
                pub_date = f"{y}-{int(m):02d}-{int(d):02d}"
            else:
                pub_date = datetime.now().strftime("%Y-%m-%d")

            description_text = category_text or f"{company} {full_title}"
            if raw_title and raw_title != full_title:
                description_text = f"{raw_title}\n{description_text}"

            job = JobItem(
                id=job_id,
                title=full_title,
                company=company,
                location=location,
                industry=industry,
                type_tags=type_tags,
                batch=batch,
                education_req=education_req,
                target_grad_year=target_grad_year,
                salary_range="面议",
                publish_date=pub_date,
                deadline=None,
                detail_url=detail_url or f"{self.LIST_URL}",
                referral_code="",
                description=description_text,
                source_site="wondercv",
                popular_level=2
            )
            jobs.append(job)

        return jobs

    async def fetch_page(self, page: int = 1, client: Optional[httpx.AsyncClient] = None) -> List[JobItem]:
        """Fetch and parse a specific page number."""
        url = f"{self.LIST_URL}" if page <= 1 else f"{self.LIST_URL}/page/pn{page}/"
        close_client = False
        if client is None:
            client = httpx.AsyncClient(headers=self.DEFAULT_HEADERS, timeout=15.0, follow_redirects=True)
            close_client = True

        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return self.parse_html_page(resp.text)
            else:
                logger.warning(f"WonderCV page {page} returned status {resp.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching WonderCV page {page}: {e}")
            return []
        finally:
            if close_client:
                await client.aclose()

    async def fetch_jobs(self, since_date: Optional[str] = None, max_pages: int = 150) -> List[JobItem]:
        """Fetch multiple pages of campus recruitment postings until since_date or max_pages."""
        all_jobs: List[JobItem] = []
        async with httpx.AsyncClient(headers=self.DEFAULT_HEADERS, timeout=15.0, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                page_jobs = await self.fetch_page(page=page, client=client)
                if not page_jobs:
                    break
                
                # Check date cutoff if since_date is specified (e.g. '2026-08-01')
                reached_cutoff = False
                for job in page_jobs:
                    if since_date and job.publish_date and job.publish_date < since_date:
                        reached_cutoff = True
                        break
                    all_jobs.append(job)
                
                if reached_cutoff:
                    logger.info(f"Reached date cutoff {since_date} on page {page}, stopping crawl.")
                    break
        return all_jobs

    async def crawl_and_save(self, since_date: Optional[str] = None, max_pages: int = 150) -> Dict[str, Any]:
        """Crawl jobs, parse into JobItems, and persist to repository."""
        jobs = await self.fetch_jobs(since_date=since_date, max_pages=max_pages)
        saved_count = 0
        if jobs:
            saved_count = await self.repo.batch_upsert(jobs)

        await self.repo.record_sync_log(
            source_site="wondercv",
            category="campus",
            items_fetched=len(jobs),
            items_inserted=saved_count,
            items_updated=0,
            status="SUCCESS" if jobs else "EMPTY",
            error_message=None if jobs else "No jobs parsed from wondercv"
        )

        return {
            "source_site": "wondercv",
            "category": "campus",
            "fetched": len(jobs),
            "saved": saved_count
        }
