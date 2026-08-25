import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"

@pytest.mark.asyncio
async def test_router_recommendation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. 自动化岗位测试
        res = await ac.get("/api/v1/router/recommend?position=运动控制算法工程师&description=负责STM32和MPC算法")
        assert res.status_code == 200
        data = res.json()
        assert data["recommended_track"] in ["控制算法版", "自动化与嵌入式版"]
        assert "MPC" in data["greeting_script"]

        # 2. 机械岗位测试
        res_mech = await ac.get("/api/v1/router/recommend?position=热设计工程师&description=负责Fluent热流仿真与腔体结构")
        assert res_mech.status_code == 200
        data_mech = res_mech.json()
        assert data_mech["recommended_track"] == "机械结构与仿真版"
        assert "Fluent" in data_mech["greeting_script"]
