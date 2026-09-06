import pytest
import os
import tempfile
from src.db import init_public_db
from src.repositories.job_repository import JobRepository
from src.services.spiders.mock_spider import MockJobSpider

@pytest.mark.asyncio
async def test_mock_spider_crawling_and_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        pub_db = os.path.join(tmpdir, "test_pub.db")
        await init_public_db(pub_db)
        job_repo = JobRepository(pub_db)

        spider = MockJobSpider()
        jobs = await spider.fetch_jobs(since_date="2026-01-01")
        assert len(jobs) > 0

        # 测试持久化入库
        upserted_count = await job_repo.batch_upsert(jobs)
        assert upserted_count == len(jobs)

        # 验证检索功能
        results, total = await job_repo.search_jobs(keyword="算法")
        assert total > 0
        assert any("算法" in j.title or "算法" in (j.description or "") for j in results)
