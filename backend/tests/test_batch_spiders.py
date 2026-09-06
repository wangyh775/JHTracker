import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.models import JobItem
from src.repositories.job_repository import JobRepository

client = TestClient(app)

def test_get_spider_sources():
    response = client.get("/api/spiders/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    source_ids = [s["id"] for s in data["sources"]]
    assert "fangzhou" in source_ids
    assert "wondercv" in source_ids
    assert "nowcoder" in source_ids

def test_batch_sync_empty_sources():
    response = client.post("/api/spiders/batch-sync", json={"sources": []})
    assert response.status_code == 400
    assert "至少指定一个" in response.json()["detail"]

@pytest.mark.asyncio
async def test_batch_sync_successful(tmp_path):
    from src.db import init_public_db
    db_path = str(tmp_path / "test_public.db")
    await init_public_db(db_path)
    test_repo = JobRepository(db_path)
    app.state.job_repo = test_repo

    fake_job = JobItem(
        id="test_batch_1",
        title="测试工程师",
        company="测试科技",
        city="北京",
        source="测试来源",
        publish_date="2026-09-01",
        detail_url="https://example.com/job/1"
    )

    with patch("src.services.spiders.fangzhou_spider.FangzhouJobSpider.fetch_jobs", new_callable=AsyncMock) as mock_fz, \
         patch("src.services.spiders.wondercv_spider.WondercvSpider.fetch_jobs", new_callable=AsyncMock) as mock_wcv:

        mock_fz.return_value = [fake_job]
        mock_wcv.return_value = [fake_job]

        response = client.post("/api/spiders/batch-sync", json={
            "sources": ["fangzhou", "wondercv"],
            "days": 15,
            "pages": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_sources"] == 2
        assert "fangzhou" in data["details"]
        assert "wondercv" in data["details"]
        assert data["details"]["fangzhou"]["success"] is True
        assert data["details"]["wondercv"]["success"] is True


@pytest.mark.asyncio
async def test_sanitize_date_str():
    from src.services.spiders.base_spider import sanitize_date_str
    assert sanitize_date_str("2026.09.04") == "2026-09-04"
    assert sanitize_date_str("2026/09/04") == "2026-09-04"
    assert sanitize_date_str("2026-09-04 12:00:00") == "2026-09-04"
    assert len(sanitize_date_str("invalid")) == 10  # fallback to today YYYY-MM-DD

