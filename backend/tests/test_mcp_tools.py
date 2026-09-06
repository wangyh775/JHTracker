"""Tests for FastMCP tool suite expansions, security hardening, and resume version isolation.
Verifies job_sync_run, job_get_detail, resume_get_profile, resume_optimize (version isolation), and input sanitization against SQL injection.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock

from src.db import init_public_db, init_user_db
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.models import JobItem, ResumeItem
import src.mcp_server as mcp_server

@pytest.fixture
async def setup_test_dbs(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        pub_db = Path(tmpdir) / "public_jobs.db"
        usr_db = Path(tmpdir) / "user_data.db"
        await init_public_db(pub_db)
        await init_user_db(usr_db)

        test_job_repo = JobRepository(pub_db)
        test_user_repo = UserRepository(usr_db)

        monkeypatch.setattr(mcp_server, "job_repo", test_job_repo)
        monkeypatch.setattr(mcp_server, "user_repo", test_user_repo)
        # Also patch repositories inside mcp_server services
        monkeypatch.setattr(mcp_server.rec_service, "job_repo", test_job_repo)
        monkeypatch.setattr(mcp_server.rec_service, "user_repo", test_user_repo)
        monkeypatch.setattr(mcp_server.resume_service, "job_repo", test_job_repo)
        monkeypatch.setattr(mcp_server.resume_service, "user_repo", test_user_repo)

        # Seed sample job
        seed_job = JobItem(
            id="test_job_001",
            title="后端架构师",
            company="方舟核心实验室",
            location="北京",
            industry="云计算",
            type_tags=["秋招", "校招"],
            batch="2026秋招",
            education_req="硕士",
            target_grad_year=["2026"],
            salary_range="30k-50k",
            publish_date="2026-09-01",
            deadline="2026-11-01",
            detail_url="https://www.qiuzhifangzhou.com/jobs/001",
            referral_code="VIP888",
            description="主导高可用分布式存储系统架构设计与实现。精通 Go / Python / Kubernetes。",
            source_site="qiuzhifangzhou",
            popular_level=5
        )
        await test_job_repo.upsert_jobs([seed_job])

        # Seed sample original resume
        seed_resume = ResumeItem(
            id="res_user_orig_001",
            title="我的主简历",
            file_path="mock/res_orig.md",
            parsed_skills=["Python", "FastAPI", "Docker"],
            content_md="# 个人主页\n精通后端开发与 API 设计。",
            version_type="ORIGINAL",
            is_default=True
        )
        await test_user_repo.save_resume(seed_resume)

        yield {
            "job_repo": test_job_repo,
            "user_repo": test_user_repo,
            "pub_db": pub_db,
            "usr_db": usr_db
        }

@pytest.mark.asyncio
async def test_mcp_job_get_detail(setup_test_dbs):
    # Valid existing job
    detail = await mcp_server.job_get_detail(job_id="test_job_001")
    assert detail["found"] is True
    assert detail["title"] == "后端架构师"
    assert detail["company"] == "方舟核心实验室"
    assert detail["referral_code"] == "VIP888"

    # Non-existent job
    missing = await mcp_server.job_get_detail(job_id="non_existing_999")
    assert missing["found"] is False
    assert "error" in missing

@pytest.mark.asyncio
async def test_mcp_job_sync_run_mocked(setup_test_dbs):
    with patch("src.services.spiders.qiuzhifangzhou_spider.QiuzhifangzhouSpider.crawl_and_save", new_callable=AsyncMock) as mock_crawl:
        mock_crawl.return_value = {
            "source_site": "qiuzhifangzhou",
            "category": "latest",
            "fetched": 15,
            "saved": 15
        }
        res = await mcp_server.job_sync_run(source="qiuzhifangzhou", category="latest", limit=15)
        assert res["success"] is True
        assert res["fetched"] == 15
        assert res["saved"] == 15

@pytest.mark.asyncio
async def test_mcp_resume_get_profile_and_optimize_isolation(setup_test_dbs):
    user_repo = setup_test_dbs["user_repo"]

    # 1. Check get_profile with explicit ID
    profile = await mcp_server.resume_get_profile(resume_id="res_user_orig_001")
    assert profile["found"] is True
    assert profile["version_type"] == "ORIGINAL"
    assert profile["is_read_only_original"] is True
    assert "Python" in profile["skills"]

    # 1.1 Check get_profile with default (no ID specified)
    default_profile = await mcp_server.resume_get_profile()
    assert default_profile["found"] is True
    assert default_profile["resume_id"] == "res_user_orig_001"

    # 2. Run resume optimization targeting test_job_001
    opt_res = await mcp_server.resume_optimize(
        resume_id="res_user_orig_001",
        job_id="test_job_001",
        optimization_type="TARGETED",
        save_as_ai_version=True
    )
    assert opt_res["success"] is True
    assert "ai_version_resume_id" in opt_res
    ai_ver_id = opt_res["ai_version_resume_id"]

    # 3. Verify original resume is completely UNCHANGED
    orig_after = await user_repo.get_resume("res_user_orig_001")
    assert orig_after.version_type == "ORIGINAL"
    assert orig_after.content_md == "# 个人主页\n精通后端开发与 API 设计。"

    # 4. Verify AI version is created separately with proper parent linkage
    ai_ver = await user_repo.get_resume(ai_ver_id)
    assert ai_ver is not None
    assert ai_ver.version_type == "AI_OPTIMIZED"
    assert ai_ver.parent_resume_id == "res_user_orig_001"
    assert "AI优化版" in ai_ver.title
    assert len(opt_res["suggestions"]) >= 1
    assert "重点突出" in opt_res["suggestions"][0] or "STAR" in opt_res["suggestions"][0]

@pytest.mark.asyncio
async def test_mcp_job_add_external_and_deduplication(setup_test_dbs):
    job_repo = setup_test_dbs["job_repo"]

    # 1. 首次录入外部检索到的岗位
    res1 = await mcp_server.job_add_external(
        title="大模型算法研究员",
        company="智算未来科技",
        location="北京",
        salary_range="35k-50k",
        detail_url="https://example.com/jobs/llm-researcher",
        description="负责前沿LLM与Agent架构研发",
        industry="人工智能",
        source_site="xiaohongshu",
        referral_code="AIAGENT2026",
        type_tags=["校招", "顶尖团队"]
    )

    assert res1["success"] is True
    job_id = res1["job_id"]
    assert job_id.startswith("ext_")

    # 验证能从公共库查询出来且字段正确
    saved_job = await job_repo.get_job_by_id(job_id)
    assert saved_job is not None
    assert saved_job.title == "大模型算法研究员"
    assert saved_job.company == "智算未来科技"
    assert saved_job.referral_code == "AIAGENT2026"
    assert "外部录入" in saved_job.type_tags
    assert "顶尖团队" in saved_job.type_tags

    # 2. 再次录入相同 公司+岗位+地点（模拟不同渠道抓到同一岗位，信息有更新）
    res2 = await mcp_server.job_add_external(
        title="大模型算法研究员",
        company="智算未来科技",
        location="北京",
        salary_range="40k-60k",  # 更新薪资
        detail_url="https://example.com/jobs/llm-researcher-v2",
        description="负责前沿LLM与Agent架构研发，要求掌握RLHF",
        industry="人工智能",
        source_site="nowcoder"
    )

    assert res2["success"] is True
    # 验证 ID 完全相同（去重哈希生效）
    assert res2["job_id"] == job_id

    # 验证数据被成功覆写更新而非新增一条
    updated_job = await job_repo.get_job_by_id(job_id)
    assert updated_job.salary_range == "40k-60k"
    assert "RLHF" in updated_job.description

    # 3. 校验入参非法校验
    bad_res = await mcp_server.job_add_external(
        title="",
        company=""
    )
    assert bad_res["success"] is False
    assert "必填项" in bad_res["error"]

@pytest.mark.asyncio
async def test_mcp_security_sanitization_and_isolation(setup_test_dbs):
    # Attempt SQL injection attack via job_id
    detail = await mcp_server.job_get_detail(job_id="' OR '1'='1; DROP TABLE jobs; --")
    assert detail["found"] is False
    assert "Invalid job_id format" in detail["error"]

    # Ensure public table is intact
    job_repo = setup_test_dbs["job_repo"]
    jobs, total = await job_repo.search_jobs()
    assert total >= 1

@pytest.mark.asyncio
async def test_mcp_job_agent_push_frequency_capping(setup_test_dbs):
    user_repo = setup_test_dbs["user_repo"]
    from src.models import ApplicationItem

    # 1. 正常推送测试
    res = await mcp_server.job_agent_push(
        job_id="test_job_001",
        recommend_reason="高匹配度核心岗位",
        match_score=0.92
    )
    assert res["success"] is True

    # 2. 模拟已投递企业：方舟核心实验室 标记为 APPLIED
    await user_repo.create_or_update_application(ApplicationItem(
        id="app_applied_test",
        job_id="test_job_001",
        company="方舟核心实验室",
        title="后端架构师",
        status="APPLIED"
    ))

    # 再次推送该企业岗位，应被已投递频控拦截
    res_applied_block = await mcp_server.job_agent_push(
        job_id="test_job_001",
        recommend_reason="重新推送已投企业"
    )
    assert res_applied_block["success"] is False
    assert "已被用户投递" in res_applied_block["error"]

    # 3. 模拟待投递企业达到 3 个上限
    for i in range(1, 4):
        await user_repo.create_or_update_application(ApplicationItem(
            id=f"app_pending_{i}",
            job_id=f"test_pending_job_{i}",
            company="超额待投公司",
            title=f"研发岗位_{i}",
            status="PENDING_APPLY"
        ))

    # 先在公共库插入该公司的岗位
    job_repo = setup_test_dbs["job_repo"]
    from src.models import JobItem
    await job_repo.insert_job(JobItem(
        id="test_pending_job_4",
        company="超额待投公司",
        title="研发岗位_4",
        location="北京",
        industry="科技",
        publish_date="2026-09-01"
    ))

    # 推送第 4 个岗位应被上限拦截
    res_capped_block = await mcp_server.job_agent_push(
        job_id="test_pending_job_4",
        recommend_reason="测试超出待投递上限"
    )
    assert res_capped_block["success"] is False
    assert "已达上限 3 个" in res_capped_block["error"]
