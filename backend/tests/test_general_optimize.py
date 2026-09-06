import pytest
from src.models import ResumeItem, ResumeOptimizeRequest
from src.services.resume_service import ResumeService
from src.repositories.user_repository import UserRepository
from src.services.resume_prompts import build_resume_optimize_prompt

@pytest.mark.asyncio
async def test_general_star_optimization(tmp_path):
    # 验证通用 STAR 润色链路的完整连通性
    user_repo = UserRepository(db_path=str(tmp_path / "test_user.db"))
    await user_repo.init_db()

    resume_service = ResumeService(user_repo=user_repo)

    # 1. 验证通用 STAR Prompt 构建
    raw_resume = "# 张三\n- 负责电商平台接口开发\n- 参与日常运维和Bug修复"
    prompt, scope = build_resume_optimize_prompt(
        resume_content=raw_resume,
        mode="GENERAL"
    )
    assert scope == "GENERAL"
    assert "STAR" in prompt
    assert "量化指标" in prompt

    # 2. 存入初始简历
    item = ResumeItem(
        id="res_general_001",
        title="张三通用简历",
        category="GENERAL",
        content_md=raw_resume,
        parsed_skills=["Python", "FastAPI"],
        is_default=True,
        version_type="ORIGINAL"
    )
    await user_repo.save_resume(item)

    # 3. 发起通用 STAR 调优请求 (未指定专岗，纯通用)
    req = ResumeOptimizeRequest(
        resume_id="res_general_001",
        mode="GENERAL",
        engine="builtin",
        save_as_version=True
    )
    res = await resume_service.optimize_resume(req)

    # 4. 断言通用 STAR 调优返回结构
    assert res["optimization_scope"] == "GENERAL"
    assert res["ats_score"] >= 80
    assert any("STAR" in s for s in res["suggestions"])
    assert any("量化" in s for s in res["suggestions"])
    assert res["is_original_protected"] is True
    assert res["optimized_resume_id"] is not None

    # 5. 验证派生的子版本正确保存并标记为 GENERAL 类
    opt_resume = await user_repo.get_resume(res["optimized_resume_id"])
    assert opt_resume is not None
    assert opt_resume.category == "GENERAL"
    assert opt_resume.version_type == "AI_OPTIMIZED"
    assert opt_resume.parent_resume_id == "res_general_001"
