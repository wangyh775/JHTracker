"""Qiuzhifangzhou Spider implementation for fetching and parsing campus and internship job postings.
Supports both JSON API and HTML fallback parsing with robust deduplication and logging.
"""
import httpx
import logging
import hashlib
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from src.models import JobItem
from src.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)

class QiuzhifangzhouSpider:
    API_URL = "https://www.qiuzhifangzhou.com/api/campus/jobs"
    PAGE_URL = "https://www.qiuzhifangzhou.com/campus"

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Referer": "https://www.qiuzhifangzhou.com/campus?table=latest"
    }

    def __init__(self, repo: Optional[JobRepository] = None):
        self.repo = repo or JobRepository()

    def generate_job_id(self, company: str, title: str, location: str, raw_id: Optional[str] = None) -> str:
        """Generate deterministic stable identifier for job."""
        if raw_id:
            if str(raw_id).startswith("qzfz_"):
                return str(raw_id)
            return f"qzfz_{raw_id}"
        unique_str = f"{company.strip()}_{title.strip()}_{location.strip()}"
        return f"qzfz_{hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12]}"

    def _parse_api_item(self, item: Dict[str, Any]) -> JobItem:
        title = item.get("title") or item.get("name") or "招聘岗位"
        company = item.get("company") or item.get("corp_name") or "知名企业"
        location = item.get("city") or item.get("location") or "全国"
        raw_id = str(item.get("id")) if item.get("id") else None

        job_id = self.generate_job_id(company, title, location, raw_id)
        
        type_tags = []
        raw_type = item.get("type") or item.get("category")
        if raw_type:
            if isinstance(raw_type, list):
                type_tags.extend(raw_type)
            else:
                type_tags.append(str(raw_type))
        
        grad_year = item.get("grad_year") or item.get("target_grad_year")
        target_grad_year = grad_year if isinstance(grad_year, list) else ([str(grad_year)] if grad_year else [])

        publish_date = item.get("publish_date") or item.get("date") or datetime.now().strftime("%Y-%m-%d")

        batch = item.get("batch")
        if not batch:
            for t in type_tags:
                if any(k in t for k in ["秋招", "春招", "实习", "提前批", "届"]):
                    batch = t
                    break
        if not batch and title:
            import re
            match = re.search(r"\[(.*?)\]", title)
            if match:
                batch = match.group(1)

        return JobItem(
            id=job_id,
            title=title,
            company=company,
            location=location,
            industry=item.get("industry") or "互联网/技术",
            type_tags=type_tags or ["校招"],
            batch=batch or "最新校招",
            education_req=item.get("education") or item.get("education_req") or "不限",
            target_grad_year=target_grad_year,
            salary_range=item.get("salary") or item.get("salary_range") or "面议",
            publish_date=publish_date,
            deadline=item.get("deadline"),
            detail_url=item.get("detail_url") or item.get("url") or f"https://www.qiuzhifangzhou.com/campus?table=latest",
            referral_code=item.get("referral_code") or "",
            description=item.get("description") or item.get("desc") or "",
            source_site="qiuzhifangzhou",
            popular_level=int(item.get("popular_level") or 1)
        )

    def _parse_html(self, html_content: str) -> List[JobItem]:
        soup = BeautifulSoup(html_content, "html.parser")
        jobs: List[JobItem] = []
        
        cards = soup.select(".job-card, .table-row, tr.job-item, div[data-job-id]")
        if not cards:
            cards = soup.select("tr")

        for card in cards:
            title_elem = card.select_one(".job-title, .title, a[href*='job']")
            company_elem = card.select_one(".company-name, .company, .corp")
            
            if not title_elem or not company_elem:
                continue

            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True)
            location_elem = card.select_one(".job-city, .city, .location")
            location = location_elem.get_text(strip=True) if location_elem else "全国"
            
            salary_elem = card.select_one(".job-salary, .salary")
            salary = salary_elem.get_text(strip=True) if salary_elem else "面议"

            batch_elem = card.select_one(".job-batch, .batch")
            batch = batch_elem.get_text(strip=True) if batch_elem else "校招"

            date_elem = card.select_one(".job-date, .date, .publish-date")
            pub_date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")

            desc_elem = card.select_one(".job-desc, .desc")
            desc = desc_elem.get_text(strip=True) if desc_elem else ""

            raw_id = card.get("data-id") or card.get("data-job-id")
            job_id = self.generate_job_id(company, title, location, raw_id)

            jobs.append(JobItem(
                id=job_id,
                title=title,
                company=company,
                location=location,
                industry="综合",
                type_tags=[batch] if batch else ["校招"],
                batch=batch,
                education_req="不限",
                target_grad_year=[],
                salary_range=salary,
                publish_date=pub_date,
                deadline=None,
                detail_url=title_elem.get("href") or "https://www.qiuzhifangzhou.com/campus?table=latest",
                referral_code="",
                description=desc,
                source_site="qiuzhifangzhou",
                popular_level=1
            ))
        return jobs

    async def fetch_raw_data(self, table: str = "latest", page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """Fetch jobs from Qiuzhifangzhou API or fallback page."""
        async with httpx.AsyncClient(headers=self.DEFAULT_HEADERS, timeout=12.0) as client:
            try:
                # 1. Attempt JSON API
                params = {"table": table, "page": page, "page_size": page_size}
                resp = await client.get(self.API_URL, params=params)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                            return data["data"]
                        elif isinstance(data, list):
                            return data
                    except Exception as json_err:
                        logger.warning(f"Failed to parse JSON response from {self.API_URL}: {json_err}")
            except Exception as e:
                logger.warning(f"Error fetching API {self.API_URL}: {e}")

            # 2. Fallback to HTML page fetch
            try:
                html_resp = await client.get(f"{self.PAGE_URL}?table={table}")
                if html_resp.status_code == 200:
                    parsed_jobs = self._parse_html(html_resp.text)
                    return [j.model_dump() for j in parsed_jobs]
            except Exception as e:
                logger.error(f"Error fetching HTML page {self.PAGE_URL}: {e}")

        return []

    async def crawl_and_save(self, table: str = "latest", limit: int = 100) -> Dict[str, Any]:
        """Crawl jobs, parse them into JobItems, and save idempotently to database."""
        raw_items = await self.fetch_raw_data(table=table, page_size=limit)
        jobs: List[JobItem] = []
        for raw in raw_items:
            try:
                if isinstance(raw, dict) and "source_site" in raw and raw["source_site"] == "qiuzhifangzhou":
                    jobs.append(JobItem(**raw))
                else:
                    jobs.append(self._parse_api_item(raw))
            except Exception as e:
                logger.warning(f"Skipping malformed job item: {e}")

        saved_count = 0
        if jobs:
            saved_count = await self.repo.batch_upsert(jobs)

        await self.repo.record_sync_log(
            source_site="qiuzhifangzhou",
            category=table,
            items_fetched=len(raw_items),
            items_inserted=saved_count,
            items_updated=0,
            status="SUCCESS" if jobs else "EMPTY",
            error_message=None if jobs else "No jobs parsed from source"
        )

        return {
            "source_site": "qiuzhifangzhou",
            "category": table,
            "fetched": len(raw_items),
            "saved": saved_count
        }
