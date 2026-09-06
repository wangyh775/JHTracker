import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.models import JobItem
from src.repositories.job_repository import JobRepository
from src.db import init_public_db

@pytest.mark.asyncio
async def test_jobs_api_filtering(tmp_path):
    db_path = str(tmp_path / "test_public.db")
    await init_public_db(db_path)
    repo = JobRepository(db_path)
    app.state.job_repo = repo

    # Seed test jobs
    j1 = JobItem(
        id="j1",
        title="后端开发工程师",
        company="腾讯科技",
        location="深圳",
        industry="互联网/游戏",
        type_tags=["校招", "大厂"],
        batch="2026届春招",
        salary_range="18-30k",
        publish_date="2026-03-01",
        referral_code="TX2026",
        source_site="qiuzhifangzhou"
    )
    j2 = JobItem(
        id="j2",
        title="算法实习生",
        company="国家电网",
        location="北京",
        industry="国企/电力",
        type_tags=["国企", "实习"],
        batch="暑期实习",
        salary_range="300/天",
        publish_date="2026-03-02",
        referral_code=None,
        source_site="qiuzhifangzhou"
    )
    await repo.upsert_jobs([j1, j2])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 1: all jobs
        resp = await client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

        # Test 2: filter by city
        resp = await client.get("/api/jobs?city=深圳")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["company"] == "腾讯科技"

        # Test 3: filter by has_referral
        resp = await client.get("/api/jobs?has_referral=true")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["referral_code"] == "TX2026"

        # Test 4: filter by category=intern
        resp = await client.get("/api/jobs?category=intern")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["company"] == "国家电网"
