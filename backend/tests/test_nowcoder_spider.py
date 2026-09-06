import pytest
import os
import tempfile
from src.db import init_public_db
from src.repositories.job_repository import JobRepository
from src.services.spiders.nowcoder_spider import NowcoderSpider

SAMPLE_NOWCODER_RECORD = {
    "companyId": 12345,
    "name": "华为HUAWEI",
    "batchName": "2027届秋招",
    "customWangshenLink": "https://career.huawei.com/reccam/campus.html",
    "sourceInformation": None,
    "cityList": ["深圳", "北京", "上海"],
    "industryList": ["通信/网络", "智能硬件"],
    "careerNameList": ["后端开发工程师", "AI算法研究员"],
    "updateTime": 1788600000000,
    "wangshenEndDate": 1799900000000,
    "referralCode": "HW8888",
    "companyEvaluation": "全球领先的信息与通信技术解决方案供应商",
}


def test_nowcoder_record_parsing():
    spider = NowcoderSpider()
    jobs = spider.parse_schedule_card(SAMPLE_NOWCODER_RECORD)

    # 2 career names should yield 2 independent JobItem
    assert len(jobs) == 2

    job1 = jobs[0]
    assert job1.company == "华为HUAWEI"
    assert "后端开发工程师" in job1.title
    assert "2027届秋招" in job1.batch
    assert "深圳、北京、上海" == job1.location
    assert job1.industry == "通信/网络"
    assert job1.source_site == "nowcoder"
    assert job1.detail_url == "https://career.huawei.com/reccam/campus.html"
    assert job1.referral_code == "HW8888"
    assert "全球领先" in job1.description
    assert job1.id.startswith("nc_")

    job2 = jobs[1]
    assert "AI算法研究员" in job2.title
    assert job2.id != job1.id


@pytest.mark.asyncio
async def test_nowcoder_storage_and_fts_indexing():
    with tempfile.TemporaryDirectory() as tmpdir:
        pub_db = os.path.join(tmpdir, "test_pub_nc.db")
        await init_public_db(pub_db)
        job_repo = JobRepository(pub_db)

        spider = NowcoderSpider(repo=job_repo)
        jobs = spider.parse_schedule_card(SAMPLE_NOWCODER_RECORD)
        assert len(jobs) == 2

        inserted = await job_repo.upsert_jobs(jobs)
        assert inserted == 2

        # Verify search works for Nowcoder jobs
        search_res, total = await job_repo.search_jobs(keyword="算法研究员", limit=10)
        assert total == 1
        assert len(search_res) == 1
        assert search_res[0].company == "华为HUAWEI"
        assert "AI算法研究员" in search_res[0].title
        assert search_res[0].source_site == "nowcoder"

        # Verify idempotency
        inserted2 = await job_repo.upsert_jobs(jobs)
        assert inserted2 == 2
