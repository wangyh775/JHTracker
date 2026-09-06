import pytest
import pytest_asyncio
import tempfile
import os
import aiosqlite
from pathlib import Path

from src.db import init_public_db, init_user_db
from src.models import JobItem
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserDataRepository
from src.services.recommendation_service import RecommendationService

@pytest_asyncio.fixture
async def setup_env():
    temp_dir = tempfile.TemporaryDirectory()
    pub_path = Path(temp_dir.name) / "test_public.db"
    user_path = Path(temp_dir.name) / "test_user.db"

    await init_public_db(pub_path)
    await init_user_db(user_path)

    j_repo = JobRepository(pub_path)
    u_repo = UserDataRepository(user_path)

    yield {"pub_path": pub_path, "user_path": user_path, "j_repo": j_repo, "u_repo": u_repo}
    temp_dir.cleanup()

@pytest.mark.asyncio
async def test_agent_push_lifecycle(setup_env):
    u_repo = setup_env["u_repo"]
    j_repo = setup_env["j_repo"]

    # 1. 插入一个测试岗位
    job = JobItem(
        id="job_agent_001",
        title="AI 大模型算法研发工程师",
        company="智谱AI",
        location="北京",
        industry="人工智能",
        publish_date="2026-09-01",
        description="负责大模型与强化学习算法研发，熟悉 Python 与 PyTorch"
    )
    await j_repo.upsert_job(job)

    # 2. 智能体执行特推
    push_id = await u_repo.add_agent_push(
        job_id="job_agent_001",
        recommend_reason="该岗位与您的深度学习/PyTorch背景高度匹配，且属于当前头部核心团队",
        match_score=0.98,
        agent_name="JobSourcingAgent"
    )
    assert push_id is not None

    # 3. 列出特推
    pushes = await u_repo.list_agent_pushes()
    assert len(pushes) == 1
    assert pushes[0]["job_id"] == "job_agent_001"
    assert pushes[0]["match_score"] == 0.98
    assert "深度学习" in pushes[0]["recommend_reason"]

    from src.models import FeedbackRequest
    # 4. 用户交互反馈 (接受该岗位) 后，该特推应自动消失在未处理流中
    fb = FeedbackRequest(
        job_id="job_agent_001",
        action="ACCEPT",
        match_score=0.98,
        recommend_reason="智能体特推"
    )
    await u_repo.record_feedback(
        feedback=fb,
        job_company="智谱AI",
        job_tags=["Python", "PyTorch"],
        job_industry="人工智能",
        job_categories=["算法/AI类"],
        job_city="北京"
    )
    pushes_after = await u_repo.list_agent_pushes()
    assert len(pushes_after) == 0
