import pytest
import os
import shutil
from pathlib import Path
from src.config import AppConfig
from src.db import init_public_db, init_user_db
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserDataRepository
from src.models import JobItem, ApplicationItem, FeedbackRequest

@pytest.fixture
async def test_env(tmp_path):
    test_user_dir = tmp_path / "user_dir"
    test_public_dir = tmp_path / "public_dir"
    test_user_dir.mkdir()
    test_public_dir.mkdir()

    user_db = test_user_dir / "user_data.db"
    public_db = test_public_dir / "public_jobs.db"

    await init_public_db(public_db)
    await init_user_db(user_db)

    job_repo = JobRepository(public_db)
    user_repo = UserDataRepository(user_db)

    return {
        "user_db": user_db,
        "public_db": public_db,
        "job_repo": job_repo,
        "user_repo": user_repo
    }

@pytest.mark.asyncio
async def test_data_isolation_and_operations(test_env):
    job_repo: JobRepository = test_env["job_repo"]
    user_repo: UserDataRepository = test_env["user_repo"]

    # 1. Insert Public Job
    job = JobItem(
        id="job_001",
        title="前端开发工程师",
        company="示例科技",
        location="北京",
        industry="互联网",
        type_tags=["上市", "外企"],
        publish_date="2026-09-01",
        description="熟练掌握 React / TypeScript"
    )
    await job_repo.upsert_job(job)

    fetched_job = await job_repo.get_job_by_id("job_001")
    assert fetched_job is not None
    assert fetched_job.company == "示例科技"

    # 2. Insert Private User Application
    app = ApplicationItem(
        id="app_001",
        job_id="job_001",
        company="示例科技",
        title="前端开发工程师",
        status="PENDING_APPLY",
        channel="官网网申"
    )
    await user_repo.create_or_update_application(app)

    apps = await user_repo.list_applications()
    assert len(apps) == 1
    assert apps[0].id == "app_001"
    assert apps[0].company == "示例科技"

    # 3. Test HITL Reject Feedback & Penalty
    fb = FeedbackRequest(
        job_id="job_001",
        action="REJECT",
        reject_reasons=["公司偏远"]
    )
    await user_repo.record_feedback(
        fb,
        job_company="示例科技",
        job_tags=["上市", "外企"],
        job_industry="互联网",
        job_categories=["软件研发类"],
        job_city="北京"
    )

    weights = await user_repo.get_all_feature_weights()
    assert "category:软件研发类" in weights
    assert weights["category:软件研发类"] <= 0.80
    assert "industry:互联网" in weights
    assert "city:北京" in weights
