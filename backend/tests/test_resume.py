import pytest
import os
import tempfile
from unittest.mock import patch, AsyncMock
from datetime import datetime
from src.db import init_public_db, init_user_db
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.resume_service import ResumeService
from src.services.agent_executor import AgentExecutor
from src.models import ResumeItem, JobItem

@pytest.mark.asyncio
async def test_agent_detector():
    """测试智能体探活逻辑"""
    agents_info = AgentExecutor.detect_available_agents()
    assert "agents" in agents_info
    assert "recommended" in agents_info
    assert any(a["id"] == "builtin" for a in agents_info["agents"])

@pytest.mark.asyncio
async def test_resume_service_optimization():
    with tempfile.TemporaryDirectory() as tmpdir:
        pub_db = os.path.join(tmpdir, "test_pub.db")
        user_db = os.path.join(tmpdir, "test_user.db")
        await init_public_db(pub_db)
        await init_user_db(user_db)

        job_repo = JobRepository(pub_db)
        user_repo = UserRepository(user_db)
        resume_service = ResumeService(job_repo, user_repo)

        # 1. 插入简历
        res_id = "res-test-01"
        await user_repo.save_resume(ResumeItem(
            id=res_id,
            title="通用简历_v1",
            category="GENERAL",
            file_path="resumes/res-test-01.md",
            content_md="# 个人简历\n熟练掌握 Python、FastAPI 及 Docker，具有微服务开发经验。",
            parsed_skills=["Python", "FastAPI", "Docker"]
        ))

        # 2. 插入目标岗位
        job = JobItem(
            id="job-target-01",
            title="高级后端架构师",
            company="前沿云科技",
            location="杭州",
            publish_date=datetime.now().strftime("%Y-%m-%d"),
            source_site="MOCK",
            description="熟练掌握 Python、FastAPI、Docker，并且具备 微服务 和 性能优化 经验。",
            type_tags=["Python", "FastAPI", "Docker", "微服务", "性能优化"]
        )
        await job_repo.upsert_jobs([job])

        # 3. 通用润色优化测试 (GENERAL)
        res_general = await resume_service.optimize_resume(
            resume_id=res_id,
            optimization_type="GENERAL"
        )
        assert res_general["ats_score"] > 0
        assert len(res_general["suggestions"]) > 0
        assert res_general["optimization_scope"] == "GENERAL"

        # 4. 专岗定制定向优化测试 - 岗位 + 企业双重 (DUAL)
        res_targeted = await resume_service.optimize_resume(
            resume_id=res_id,
            job_id="job-target-01",
            optimization_type="TARGETED",
            save_as_version=True
        )
        assert res_targeted["target_company"] == "前沿云科技"
        assert res_targeted["optimization_scope"] == "DUAL"
        assert "性能优化" in res_targeted["missing_keywords"]
        assert "Python" in res_targeted["matched_keywords"]
        assert res_targeted.get("optimized_resume_id") is not None

        # 验证专岗子版本已独立存入，未覆写母版
        saved_ai_version = await user_repo.get_resume(res_targeted["optimized_resume_id"])
        assert saved_ai_version is not None
        assert saved_ai_version.version_type == "AI_OPTIMIZED"
        assert saved_ai_version.parent_resume_id == res_id

        # 5. 专岗 - 仅企业维度调优 (COMPANY)
        res_company = await resume_service.optimize_resume(
            resume_id=res_id,
            optimization_type="TARGETED",
            target_company="阿里巴巴"
        )
        assert res_company["target_company"] == "阿里巴巴"
        assert res_company["optimization_scope"] == "COMPANY"

        # 6. 专岗 - 仅岗位维度调优 (POSITION)
        res_position = await resume_service.optimize_resume(
            resume_id=res_id,
            optimization_type="TARGETED",
            target_position="分布式存储开发工程师"
        )
        assert res_position["target_position"] == "分布式存储开发工程师"
        assert res_position["optimization_scope"] == "POSITION"

        # 7. Mock 本地智能体返回测试
        mock_agent_return = {
            "ats_score": 92,
            "match_level": "HIGH",
            "matched_keywords": ["Python", "FastAPI"],
            "missing_keywords": ["Ceph"],
            "suggestions": ["强化底层存储性能数据"],
            "optimized_markdown": "# 智能体量化改写后的简历正文",
            "_engine_used": "Hermes Agent"
        }
        with patch.object(AgentExecutor, "execute_prompt", AsyncMock(return_value=mock_agent_return)):
            res_agent = await resume_service.optimize_resume(
                resume_id=res_id,
                optimization_type="TARGETED",
                target_position="Ceph 存储研发",
                engine="hermes"
            )
            assert res_agent["ats_score"] == 92
            assert res_agent["engine_used"] == "Hermes Agent"
            assert "Ceph" in res_agent["missing_keywords"]

        # 8. 测试自定义 LLM 配置与 HTTP 执行通道
        from src.models import LLMConfig
        custom_llm_cfg = LLMConfig(
            base_url="http://127.0.0.1:8045/v1",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )
        await user_repo.set_setting("custom_llm_config", custom_llm_cfg.model_dump_json())
        saved_setting = await user_repo.get_setting("custom_llm_config")
        assert "claude-3-5-sonnet-20241022" in saved_setting

        mock_http_return = {
            "ats_score": 95,
            "match_level": "HIGH",
            "matched_keywords": ["Python", "AsyncIO"],
            "missing_keywords": ["Kubernetes"],
            "suggestions": ["补充容器编排实战"],
            "optimized_markdown": "# LLM 直连优化简历",
            "_engine_used": "LLM 直连 (claude-3-5-sonnet-20241022)"
        }
        with patch.object(AgentExecutor, "execute_via_http", AsyncMock(return_value=mock_http_return)):
            res_llm = await resume_service.optimize_resume(
                resume_id=res_id,
                optimization_type="TARGETED",
                target_position="云原生后端",
                engine="custom_api"
            )
            assert res_llm["ats_score"] == 95
            assert "LLM 直连" in res_llm["engine_used"]

        # 9. 测试删除简历功能
        del_success = await user_repo.delete_resume(res_id)
        assert del_success is True
        fetched_after_del = await user_repo.get_resume(res_id)
        assert fetched_after_del is None
