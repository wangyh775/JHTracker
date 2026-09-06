"""Unit & integration tests for Qiuzhifangzhou crawler pipeline,
including API parsing, HTML fallback extraction, field normalization, and database idempotent upsert.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from src.services.spiders.qiuzhifangzhou_spider import QiuzhifangzhouSpider
from src.models import JobItem
from src.db import init_public_db, get_public_db
from src.repositories.job_repository import JobRepository

MOCK_API_RESPONSE = {
    "code": 0,
    "data": [
        {
            "id": "qzfz_mock_001",
            "title": "后端开发工程师（校招）",
            "company": "方舟科技",
            "city": "北京/上海",
            "industry": "互联网/软件",
            "type": "秋招",
            "education": "本科及以上",
            "grad_year": ["2026", "2027"],
            "salary": "15k-25k",
            "publish_date": "2026-09-01",
            "deadline": "2026-11-30",
            "detail_url": "https://www.qiuzhifangzhou.com/jobs/001",
            "referral_code": "FZ2026",
            "description": "精通 Python 或 Golang，掌握 SQLite/MySQL 调优。"
        },
        {
            "id": "qzfz_mock_002",
            "title": "国企管培生",
            "company": "中国通信设备集团",
            "city": "深圳",
            "industry": "通信/国企",
            "type": "校招",
            "education": "硕士",
            "grad_year": ["2026"],
            "salary": "18k-30k",
            "publish_date": "2026-09-02",
            "detail_url": "https://www.qiuzhifangzhou.com/jobs/002",
            "referral_code": "",
            "description": "计算机、通信及相关专业应届毕业生。"
        }
    ]
}

MOCK_HTML_PAGE = """
<!DOCTYPE html>
<html>
<body>
  <div class="job-card" data-id="html_job_101">
    <h3 class="job-title"><a href="/jobs/101">AI算法工程师</a></h3>
    <div class="company-name">智能方舟研究院</div>
    <div class="job-city">杭州</div>
    <div class="job-salary">25k-40k</div>
    <div class="job-batch">2027届实习</div>
    <div class="job-date">2026-09-03</div>
    <p class="job-desc">负责推荐系统与大模型推理优化。</p>
  </div>
</body>
</html>
"""

def test_parse_api_item_normalization():
    spider = QiuzhifangzhouSpider()
    raw_item = MOCK_API_RESPONSE["data"][0]
    job = spider._parse_api_item(raw_item)

    assert isinstance(job, JobItem)
    assert job.id == "qzfz_mock_001"
    assert job.title == "后端开发工程师（校招）"
    assert job.company == "方舟科技"
    assert job.location == "北京/上海"
    assert job.salary_range == "15k-25k"
    assert job.publish_date == "2026-09-01"
    assert job.source_site == "qiuzhifangzhou"
    assert "秋招" in job.type_tags
    assert job.referral_code == "FZ2026"

def test_parse_html_fallback():
    spider = QiuzhifangzhouSpider()
    jobs = spider._parse_html(MOCK_HTML_PAGE)

    assert len(jobs) >= 1
    job = jobs[0]
    assert job.title == "AI算法工程师"
    assert job.company == "智能方舟研究院"
    assert job.location == "杭州"
    assert job.salary_range == "25k-40k"
    assert job.source_site == "qiuzhifangzhou"

@pytest.mark.asyncio
async def test_crawler_fetch_and_idempotent_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "public_jobs.db"
        await init_public_db(db_path)
        repo = JobRepository(db_path=db_path)
        spider = QiuzhifangzhouSpider(repo=repo)

        # Mock network fetch
        with patch.object(spider, "fetch_raw_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_API_RESPONSE["data"]

            # First run: 2 jobs inserted
            result1 = await spider.crawl_and_save(table="latest", limit=10)
            assert result1["fetched"] == 2
            assert result1["saved"] == 2

            jobs, total = await repo.search_jobs(keyword="方舟科技")
            assert total == 1
            assert jobs[0].title == "后端开发工程师（校招）"

            # Second run with same data: Idempotent upsert (0 duplicates inserted)
            result2 = await spider.crawl_and_save(table="latest", limit=10)
            assert result2["fetched"] == 2
            assert result2["saved"] == 2

            # Check total records in db remains 2
            async with get_public_db(db_path) as db:
                async with db.execute("SELECT COUNT(*) FROM jobs") as cur:
                    count_row = await cur.fetchone()
                    assert count_row[0] == 2
