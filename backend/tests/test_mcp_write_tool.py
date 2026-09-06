# test_mcp_write_tool.py
import pytest
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from src.mcp_server import job_add_external, job_sync_run
from src.repositories.job_repository import JobRepository
from src.config import settings

@pytest.mark.asyncio
async def test_job_add_external_mapping():
    result = await job_add_external(
        title="AI研发工程师",
        company="测试科技有限公司",
        location="北京、上海",
        salary_range="25k-40k",
        detail_url="https://example.com/job/123",
        description="岗位详细描述，要求精通Python和FastAPI",
        industry="人工智能",
        source_site="agent_search",
        referral_code="INT666",
        type_tags=["校招", "算法", "急聘"]
    )
    assert result["success"] is True
    job_id = result["job_id"]
    assert job_id.startswith("ext_")

    repo = JobRepository(settings.public_db_path)
    job = await repo.get_job_by_id(job_id)
    assert job is not None
    assert job.title == "AI研发工程师"
    assert job.company == "测试科技有限公司"
    assert job.location == "北京、上海"
    assert job.salary_range == "25k-40k"
    assert job.detail_url == "https://example.com/job/123"
    assert job.industry == "人工智能"
    assert job.source_site == "agent_search"
    assert job.referral_code == "INT666"
    assert "外部录入" in job.type_tags
    assert "急聘" in job.type_tags

    # Clean up test row
    import aiosqlite
    async with aiosqlite.connect(settings.public_db_path) as db:
        await db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        await db.execute("DELETE FROM jobs_fts WHERE rowid IN (SELECT rowid FROM jobs WHERE id = ?)", (job_id,))
        await db.commit()
