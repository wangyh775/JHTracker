"""Nowcoder (牛客网) Campus Recruitment Spider.
Extracts structured company, batch, title, location, industry, career tags, deadline,
and direct company application links from Nowcoder's campus recruitment portal.
"""
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from src.models import JobItem
from src.repositories.job_repository import JobRepository
from src.services.spiders.base_spider import BaseJobSpider

logger = logging.getLogger(__name__)


class NowcoderSpider(BaseJobSpider):
    """Spider implementation for fetching campus recruitment data from Nowcoder (牛客网)."""

    BASE_URL = "https://www.nowcoder.com"
    SCHEDULE_API = "https://www.nowcoder.com/np-api/u/school-schedule/list-card"
    SQUARE_API = "https://www.nowcoder.com/np-api/u/job/square-search"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.nowcoder.com/jobs/school/schedule",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    def __init__(self, repo: Optional[JobRepository] = None):
        self.repo = repo or JobRepository()

    def generate_job_id(self, company: str, title: str, batch: str = "", raw_id: Optional[str] = None) -> str:
        """Generate deterministic stable identifier for Nowcoder jobs."""
        if raw_id:
            cleaned_id = str(raw_id).strip().replace("/", "_")
            if cleaned_id.startswith("nc_"):
                return cleaned_id
            return f"nc_{cleaned_id}"
        unique_str = f"nowcoder_{company.strip()}_{title.strip()}_{batch.strip()}"
        return f"nc_{hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12]}"

    def parse_schedule_card(self, item: Dict[str, Any]) -> List[JobItem]:
        """Convert a single schedule record into one or more JobItem models.
        
        If multiple career titles exist, generates independent JobItem per title.
        """
        company = (item.get("name") or "").strip()
        if not company:
            return []

        company_id = item.get("companyId")
        batch = (item.get("batchName") or "").strip()
        ad_info = item.get("adInfo") or {}

        # Resolve direct application link
        detail_url = (
            item.get("customWangshenLink")
            or item.get("sourceInformation")
            or ad_info.get("rawUrl")
            or (f"https://www.nowcoder.com/company/home/{company_id}/schedule" if company_id else "https://www.nowcoder.com/jobs/school/schedule")
        ).strip()

        # Location parsing
        city_list = item.get("cityList") or []
        location = "、".join(city_list) if city_list else "全国"

        # Industry parsing
        industry_list = item.get("industryList") or []
        industry = industry_list[0] if industry_list else "互联网/软件"

        # Dates
        update_timestamp = item.get("updateTime") or item.get("wangshenUpdateTime") or item.get("wangshenBeginDate")
        if update_timestamp:
            publish_date = datetime.fromtimestamp(update_timestamp / 1000).strftime("%Y-%m-%d")
        else:
            publish_date = datetime.now().strftime("%Y-%m-%d")

        end_timestamp = item.get("wangshenEndDate")
        deadline = datetime.fromtimestamp(end_timestamp / 1000).strftime("%Y-%m-%d") if end_timestamp else None

        referral_code = (item.get("referralCode") or "").strip()
        evaluation = (item.get("companyEvaluation") or "").strip()

        # Type tags
        type_tags = ["校招", "牛客精选"]
        if not deadline:
            type_tags.append("招满即止")
        if batch:
            type_tags.append(batch)
        if industry_list:
            type_tags.extend(industry_list[:2])

        career_names = item.get("careerNameList") or []
        if not career_names:
            career_names = [f"{company}{batch or '校园招聘'}"]

        job_items: List[JobItem] = []
        for career in career_names:
            career_clean = str(career).strip()
            if not career_clean:
                continue

            title = f"{career_clean}（{batch}）" if batch and batch not in career_clean else career_clean
            raw_id = f"{company_id}_{hashlib.md5(career_clean.encode('utf-8')).hexdigest()[:6]}" if company_id else None
            job_id = self.generate_job_id(company=company, title=career_clean, batch=batch, raw_id=raw_id)

            desc_parts = []
            if evaluation:
                desc_parts.append(f"【公司简介】{evaluation}")
            desc_parts.append(f"【招聘批次】{batch or '2026/2027届校园招聘'}")
            desc_parts.append(f"【招聘岗位】{career_clean}")
            if city_list:
                desc_parts.append(f"【工作地点】{location}")
            if referral_code:
                desc_parts.append(f"【内推码】{referral_code}")
            desc_parts.append(f"【网申渠道】{detail_url}")

            target_grad_year = []
            if "2027" in batch or "27" in batch:
                target_grad_year.append("2027")
            if "2026" in batch or "26" in batch:
                target_grad_year.append("2026")
            if not target_grad_year:
                target_grad_year = ["2026", "2027"]

            job = JobItem(
                id=job_id,
                title=title,
                company=company,
                location=location,
                industry=industry,
                type_tags=list(set(type_tags + [career_clean])),
                batch=batch or "校园招聘",
                education_req="本科及以上",
                target_grad_year=target_grad_year,
                salary_range="面议",
                publish_date=publish_date,
                deadline=deadline,
                detail_url=detail_url,
                referral_code=referral_code,
                description="\n".join(desc_parts),
                source_site="nowcoder",
                popular_level=4 if ("27" in batch or "秋招" in batch) else 3,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            job_items.append(job)

        return job_items

    async def fetch_jobs(
        self,
        since_date: str = "2026-07-01",
        max_pages: int = 10,
        page_size: int = 50,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[JobItem]:
        """Fetch campus schedule recruitment postings from Nowcoder.
        
        Args:
            since_date: Earliest publish date filter in 'YYYY-MM-DD' format.
            max_pages: Maximum number of pages to traverse.
            page_size: Number of items per request page (recommended 20~100).
            client: Optional httpx.AsyncClient instance.
        """
        all_jobs: List[JobItem] = []
        should_close = False
        if client is None:
            client = httpx.AsyncClient(headers=self.DEFAULT_HEADERS, timeout=15.0, follow_redirects=True)
            should_close = True

        try:
            for page in range(1, max_pages + 1):
                payload = {
                    "page": page,
                    "pageSize": page_size,
                }
                logger.info("Fetching Nowcoder campus schedule page %d (size=%d)...", page, page_size)

                try:
                    resp = await client.post(self.SCHEDULE_API, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as err:
                    logger.error("Failed to fetch Nowcoder schedule page %d: %s", page, err)
                    break

                if not data or data.get("code") != 0:
                    logger.warning("Nowcoder API returned non-zero code on page %d: %s", page, data.get("msg"))
                    break

                page_data = data.get("data") or {}
                datas = page_data.get("datas") or []
                if not datas:
                    logger.info("No more records returned by Nowcoder on page %d. Stopping.", page)
                    break

                reached_cutoff = False
                for record in datas:
                    parsed_jobs = self.parse_schedule_card(record)
                    for job in parsed_jobs:
                        if since_date and job.publish_date and job.publish_date < since_date:
                            reached_cutoff = True
                            continue
                        all_jobs.append(job)

                if reached_cutoff:
                    logger.info("Reached cutoff date %s at page %d. Halting pagination.", since_date, page)
                    break

        finally:
            if should_close:
                await client.aclose()

        logger.info("NowcoderSpider fetched %d valid job items in total.", len(all_jobs))
        return all_jobs

    async def run(
        self,
        since_date: str = "2026-07-01",
        max_pages: int = 10,
        page_size: int = 50,
    ) -> int:
        """Fetch jobs and upsert into database."""
        jobs = await self.fetch_jobs(since_date=since_date, max_pages=max_pages, page_size=page_size)
        if not jobs:
            return 0
        total_upserted = await self.repo.upsert_jobs(jobs)
        logger.info("NowcoderSpider sync complete: %d jobs upserted.", total_upserted)
        return total_upserted
