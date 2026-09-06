import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import tempfile
import os
from src.main import app
from src.db import init_public_db, init_user_db
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.recommendation_service import RecommendationService
from src.models import JobItem, ResumeItem, ApplicationItem, FeedbackRequest

@pytest_asyncio.fixture
async def test_client():
    with tempfile.TemporaryDirectory() as tmpdir:
        pub_db = os.path.join(tmpdir, "public_test.db")
        user_db = os.path.join(tmpdir, "user_test.db")
        await init_public_db(pub_db)
        await init_user_db(user_db)
        
        job_repo = JobRepository(db_path=pub_db)
        user_repo = UserRepository(db_path=user_db)
        rec_service = RecommendationService(job_repo=job_repo, user_repo=user_repo)
        from src.services.resume_service import ResumeService
        resume_service = ResumeService(job_repo=job_repo, user_repo=user_repo)
        
        app.state.job_repo = job_repo
        app.state.user_repo = user_repo
        app.state.rec_service = rec_service
        app.state.resume_service = resume_service
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, job_repo, user_repo

@pytest.mark.asyncio
async def test_get_jobs_api(test_client):
    client, job_repo, _ = test_client
    await job_repo.upsert_job(JobItem(
        id="job-api-1",
        title="API Test Engineer",
        company="TechCorp",
        location="北京",
        industry="互联网",
        publish_date="2026-06-01"
    ))
    res = await client.get("/api/jobs?keyword=API")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == "job-api-1"

@pytest.mark.asyncio
async def test_tracker_overview_api(test_client):
    client, _, user_repo = test_client
    await user_repo.save_application(ApplicationItem(
        id="app-1",
        job_id="job-1",
        company="Alpha",
        title="Dev",
        status="APPLIED",
        applied_at="2026-06-01"
    ))
    res = await client.get("/api/tracker/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_applications"] == 1
    assert data["status_distribution"].get("APPLIED") == 1

@pytest.mark.asyncio
async def test_resumes_crud_and_optimize_api(test_client):
    client, job_repo, user_repo = test_client
    
    # 1. 创建简历 (测试 payload 包含 content_markdown, skills, 没有 file_path)
    create_payload = {
        "title": "前端开发工程师简历",
        "category": "GENERAL",
        "content_markdown": "# 前端简历\n熟练掌握 React, TypeScript, Tailwind CSS",
        "skills": ["React", "TypeScript", "Tailwind CSS"],
        "is_default": True
    }
    create_res = await client.post("/api/resumes", json=create_payload)
    assert create_res.status_code == 200
    created_data = create_res.json()
    assert created_data["success"] is True
    res_id = created_data["resume"]["id"]
    assert created_data["resume"]["title"] == "前端开发工程师简历"
    assert created_data["resume"]["content_md"] == create_payload["content_markdown"]
    assert created_data["resume"]["is_default"] is True

    # 2. 查询简历列表并验证 skills 与 keywords_matrix.categories.core 自动关联
    list_res = await client.get("/api/resumes")
    assert list_res.status_code == 200
    res_list = list_res.json()
    assert len(res_list) == 1
    assert res_list[0]["content_md"] == create_payload["content_markdown"]
    assert res_list[0]["id"] == res_id
    # 验证 core 技能与 parsed_skills 同步
    assert res_list[0]["parsed_skills"] == create_payload["skills"]
    assert res_list[0]["keywords_matrix"] is not None
    core_kw = [item["keyword"] for item in res_list[0]["keywords_matrix"]["categories"]["core"]]
    assert core_kw == create_payload["skills"]

    # 3. 更新简历 (PUT /api/resumes/{id})
    update_payload = {
        "title": "资深全栈工程师简历",
        "content_markdown": "# 全栈简历\n精通 React, TypeScript, FastAPI",
        "skills": ["React", "TypeScript", "FastAPI"]
    }
    update_res = await client.put(f"/api/resumes/{res_id}", json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "资深全栈工程师简历"
    assert updated_data["content_md"] == update_payload["content_markdown"]
    assert updated_data["parsed_skills"] == update_payload["skills"]
    assert updated_data["keywords_matrix"] is not None
    updated_core = [item["keyword"] for item in updated_data["keywords_matrix"]["categories"]["core"]]
    assert updated_core == update_payload["skills"]

    # 4. 优化简历 (/api/resumes/{id}/optimize)
    opt_res = await client.post(f"/api/resumes/{res_id}/optimize", json={"mode": "GENERAL", "save_as_version": True})
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["ats_score"] > 0
    assert "optimized_resume_id" in opt_data

    # 现在应该有两个版本
    list_res2 = await client.get("/api/resumes")
    assert len(list_res2.json()) == 2

    # 5. 删除简历
    del_res = await client.delete(f"/api/resumes/{res_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 验证原简历已删除
    list_res3 = await client.get("/api/resumes")
    remaining_ids = [r["id"] for r in list_res3.json()]
    assert res_id not in remaining_ids

@pytest.mark.asyncio
async def test_hitl_weights_api(test_client):
    client, _, user_repo = test_client
    await user_repo.record_feedback(
        feedback=FeedbackRequest(job_id="test-job-1", action="ACCEPT"),
        job_company="字节跳动",
        job_tags=["大厂研发"],
        job_industry="互联网",
        job_categories=["算法/AI类"],
        job_city="北京"
    )
    await user_repo.record_feedback(
        feedback=FeedbackRequest(job_id="test-job-2", action="REJECT"),
        job_company="某外包",
        job_tags=["外包运维"],
        job_industry=None,
        job_categories=["职能/HR/管理"],
        job_city="武汉"
    )

    # 1. 查询权重
    res = await client.get("/api/hitl/weights")
    assert res.status_code == 200
    data = res.json()
    assert "weights" in data
    assert "details" in data
    assert "category:算法/AI类" in data["weights"]
    assert data["weights"]["category:算法/AI类"] > 1.0
    assert len(data["details"]) >= 2

    # 2. 单项重置 (归位到 1.0x，不删除字典项)
    reset_res = await client.post("/api/hitl/weights/reset", json={"feature_key": "category:算法/AI类"})
    assert reset_res.status_code == 200
    
    res2 = await client.get("/api/hitl/weights")
    data2 = res2.json()
    assert data2["weights"]["category:算法/AI类"] == 1.0
    assert data2["weights"]["category:职能/HR/管理"] < 1.0

    # 3. 全部重置 (全部归位到 1.0x，保留字典元数据)
    reset_all_res = await client.post("/api/hitl/weights/reset", json={})
    assert reset_all_res.status_code == 200
    res3 = await client.get("/api/hitl/weights")
    data3 = res3.json()
    assert all(w == 1.0 for w in data3["weights"].values())
    assert len(data3["weights"]) >= 2

@pytest.mark.asyncio
async def test_application_archive_and_delete_api(test_client):
    client, job_repo, user_repo = test_client
    # 创建测试申请
    app = ApplicationItem(
        id="app-test-crud",
        job_id="job-crud-1",
        company="BetaTech",
        title="Python Engineer",
        status="PENDING_APPLY",
        is_archived=False
    )
    await user_repo.save_application(app)

    # 1. 默认包含归档，或者 include_archived=false 过滤测试
    apps_active = await client.get("/api/applications?include_archived=false")
    assert apps_active.status_code == 200
    assert any(a["id"] == "app-test-crud" for a in apps_active.json())

    # 2. 归档卡片
    archive_res = await client.patch("/api/applications/app-test-crud/archive", json={"is_archived": True})
    assert archive_res.status_code == 200
    assert archive_res.json()["is_archived"] is True

    # 验证非归档列表不再出现
    apps_after_archive = await client.get("/api/applications?include_archived=false")
    assert not any(a["id"] == "app-test-crud" for a in apps_after_archive.json())

    # 验证全量列表包含且 is_archived 为 True
    apps_all = await client.get("/api/applications?include_archived=true")
    target_app = next(a for a in apps_all.json() if a["id"] == "app-test-crud")
    assert target_app["is_archived"] is True

    # 3. 取消归档
    unarchive_res = await client.patch("/api/applications/app-test-crud/archive", json={"is_archived": False})
    assert unarchive_res.status_code == 200
    assert unarchive_res.json()["is_archived"] is False

    # 4. 删除卡片
    delete_res = await client.delete("/api/applications/app-test-crud")
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # 再次删除返回 404
    delete_404_res = await client.delete("/api/applications/app-test-crud")
    assert delete_404_res.status_code == 404

    # 5. 测试反馈流转接口 /api/recommendations/feedback
    # 先在 job_repo 写入岗位
    await job_repo.upsert_job(JobItem(
        id="job-feedback-1",
        title="Frontend Specialist",
        company="StarCloud",
        location="杭州",
        industry="互联网",
        publish_date="2026-06-01"
    ))
    fb_res = await client.post("/api/recommendations/feedback", json={
        "job_id": "job-feedback-1",
        "action": "ACCEPT",
        "match_score": 0.95,
        "recommend_reason": "非常契合候选人背景"
    })
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data.get("success") is True
    assert fb_data.get("action") == "ACCEPT"

    # 验证该岗位成功流转进入 applications 且状态为 PENDING_APPLY
    apps_after_fb = await client.get("/api/applications?include_archived=false")
    assert apps_after_fb.status_code == 200
    pending_app = next((a for a in apps_after_fb.json() if a.get("job_id") == "job-feedback-1"), None)
    assert pending_app is not None
    assert pending_app["status"] == "PENDING_APPLY"
    assert pending_app["company"] == "StarCloud"
    assert pending_app["match_score"] == 0.95
    assert pending_app["recommend_reason"] == "非常契合候选人背景"

@pytest.mark.asyncio
async def test_get_system_version_api(test_client):
    client, _, _ = test_client
    res = await client.get("/api/system/version")
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert data["version"] == "0.1.1"
    assert data["release_tag"] == "v0.1.1"
    assert data["app_name"] == "JHTracker"
    assert data["status"] == "online"



