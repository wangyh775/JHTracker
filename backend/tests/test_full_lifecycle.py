import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.database import init_db

@pytest.mark.asyncio
async def test_full_application_lifecycle_and_filter():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        unique_name = f"大疆创新测试公司_{uuid.uuid4().hex[:6]}"
        # 1. 创建公司
        res_comp = await ac.post("/api/v1/companies", json={"name": unique_name, "city": "深圳"})
        assert res_comp.status_code == 200
        comp_id = res_comp.json()["id"]

        # 2. 创建投递
        payload = {
            "company_id": comp_id,
            "position": "控制算法工程师",
            "status": "已投递",
            "track": "control",
            "resume_version": "王云鹤_简历_控制.pdf",
            "channel": "官网",
            "salary_min": 25,
            "salary_max": 35,
            "notes": "负责MPC模型预测控制"
        }
        res = await ac.post("/api/v1/applications", json=payload)
        assert res.status_code == 200
        app_data = res.json()
        app_id = app_data["id"]
        assert app_data["position"] == "控制算法工程师"
        assert app_data["track"] == "control"
        assert app_data["company"]["name"] == unique_name

        # 3. 活跃列表查询（默认 active=True）
        res_list = await ac.get("/api/v1/applications")
        assert res_list.status_code == 200
        items = res_list.json()["items"]
        assert any(item["id"] == app_id for item in items)

        # 4. 筛选轨道
        res_track = await ac.get("/api/v1/applications?track=control")
        assert res_track.status_code == 200
        assert all(item["track"] == "control" for item in res_track.json()["items"])

        # 5. 更新状态为 已挂（归档状态）
        res_up = await ac.put(f"/api/v1/applications/{app_id}", json={"status": "已挂", "is_archived": True})
        assert res_up.status_code == 200
        assert res_up.json()["status"] == "已挂"

        # 6. 查询活跃列表应不包含已归档
        res_active = await ac.get("/api/v1/applications?active=true")
        assert not any(item["id"] == app_id for item in res_active.json()["items"])

        # 7. 查询归档列表应包含该投递
        res_archived = await ac.get("/api/v1/applications?active=false")
        assert any(item["id"] == app_id for item in res_archived.json()["items"])

        # 8. 手动归档/解归档 API 测试
        res_unarchive = await ac.post(f"/api/v1/applications/{app_id}/unarchive")
        assert res_unarchive.status_code == 200
        assert res_unarchive.json()["is_archived"] is False

        res_archive = await ac.post(f"/api/v1/applications/{app_id}/archive")
        assert res_archive.status_code == 200
        assert res_archive.json()["is_archived"] is True

        # 9. 删除
        res_del = await ac.delete(f"/api/v1/applications/{app_id}")
        assert res_del.status_code == 200

@pytest.mark.asyncio
async def test_to_apply_and_submission_flow():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. 匹配 4 轨路由
        res_match = await ac.post("/api/v1/router/match", json={
            "job_title": "3D打印热仿真工程师",
            "job_description": "ANSYS Fluent热流固耦合及CoreXY腔体温控"
        })
        assert res_match.status_code == 200
        match_data = res_match.json()
        assert match_data["track_key"] == "mechanical_cfd"
        assert "机械结构" in match_data["track_name"]

        # 2. 查询待投递列表
        res_to_apply = await ac.get("/api/v1/to-apply")
        assert res_to_apply.status_code == 200
        items = res_to_apply.json()
        assert isinstance(items, list)

        # 3. 统计简报
        res_dash = await ac.get("/api/v1/dashboard/briefing")
        assert res_dash.status_code == 200
        dash = res_dash.json()
        assert "active_applications_count" in dash
        assert "track_distribution" in dash
