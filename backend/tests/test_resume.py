import pytest
import os
import tempfile
from datetime import datetime
from src.db import init_public_db, init_user_db
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.resume_service import ResumeService
from src.models import ResumeItem, JobItem

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

        # 3. 通用润色优化测试
        res_general = await resume_service.optimize_resume(resume_id=res_id, optimization_type="GENERAL")
        assert res_general["ats_score"] > 0
        assert len(res_general["suggestions"]) > 0

        # 4. 专岗定制定向优化测试
        res_targeted = await resume_service.optimize_resume(
            resume_id=res_id,
            job_id="job-target-01",
            optimization_type="TARGETED"
        )
        assert res_targeted["target_company"] == "前沿云科技"
        assert "性能优化" in res_targeted["missing_keywords"]
        assert "Python" in res_targeted["matched_keywords"]
        assert "专岗适配建议" in res_targeted["optimized_markdown"]

        # 5. 测试删除简历功能
        del_success = await user_repo.delete_resume(res_id)
        assert del_success is True
        fetched_after_del = await user_repo.get_resume(res_id)
        assert fetched_after_del is None
