import pytest
import os
import tempfile
from src.db import init_public_db
from src.repositories.job_repository import JobRepository
from src.services.spiders.wondercv_spider import WondercvSpider

SAMPLE_WONDERCV_HTML = """
<!DOCTYPE html>
<html>
<body>
<div class="job-list">
    <div class="job-item">
        <a class="company-name" href="/company/c123">中冶赛迪集团有限公司</a>
        <a class="job-name" href="/xiaozhao/ceri-2027-campus-recruitment-14155-53c215/">中冶赛迪2027校园招聘正式启动</a>
        <div class="job-info">
            <span>重庆</span>
            <span>硕士</span>
            <span>央企</span>
        </div>
        <div class="job-category">研发工程师/建筑设计/人工智能</div>
    </div>
    <div class="job-item">
        <a class="company-name" href="/company/c456">某头部量化私募基金</a>
        <a class="job-name" href="/xiaozhao/quant-fund-2026-campus-9988-aabb11/">2026届量化策略研究员校园招聘</a>
        <div class="job-info">
            <span>上海</span>
            <span>博士</span>
            <span>金融</span>
        </div>
        <div class="job-category">C++高性能计算/数学建模</div>
    </div>
</div>
</body>
</html>
"""

def test_wondercv_html_parsing():
    spider = WondercvSpider()
    jobs = spider.parse_html_page(SAMPLE_WONDERCV_HTML)
    assert len(jobs) == 2

    job1 = jobs[0]
    assert job1.company == "中冶赛迪集团有限公司"
    assert "2027" in job1.title
    assert job1.location == "重庆"
    assert job1.education_req == "硕士"
    assert "央企" in job1.type_tags
    assert "2027" in job1.target_grad_year
    assert "14155-53c215" in job1.id
    assert job1.source_site == "wondercv"
    assert "https://www.wondercv.com/xiaozhao/ceri-2027-campus-recruitment-14155-53c215/" in job1.detail_url

    job2 = jobs[1]
    assert job2.company == "某头部量化私募基金"
    assert "量化" in job2.title
    assert job2.location == "上海"
    assert job2.education_req == "博士"
    assert "2026" in job2.target_grad_year
    assert "9988-aabb11" in job2.id

@pytest.mark.asyncio
async def test_wondercv_storage_and_fts_indexing():
    with tempfile.TemporaryDirectory() as tmpdir:
        pub_db = os.path.join(tmpdir, "test_pub_wcv.db")
        await init_public_db(pub_db)
        job_repo = JobRepository(pub_db)

        spider = WondercvSpider(repo=job_repo)
        jobs = spider.parse_html_page(SAMPLE_WONDERCV_HTML)

        # 批量入库
        saved_count = await job_repo.batch_upsert(jobs)
        assert saved_count == 2

        # 验证 SQLite FTS5 全文索引查询能力
        results, total = await job_repo.search_jobs(keyword="量化")
        assert total == 1
        assert results[0].company == "某头部量化私募基金"

        # 验证幂等去重入库 (再次入库不重复增加)
        saved_again = await job_repo.batch_upsert(jobs)
        assert saved_again == 2
        all_jobs, all_total = await job_repo.search_jobs()
        assert all_total == 2
