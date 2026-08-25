import pytest
from backend.app.services.router import ResumeRouter

def test_4track_router_matching():
    # 1. Control track
    track, name, pdf, greeting, skills, conf = ResumeRouter.resolve_track(
        "控制算法工程师", "负责MPC模型预测控制与EKF滤波"
    )
    assert track == "control"
    assert "控制算法版" in name
    assert "王云鹤_简历_控制.pdf" in pdf
    assert "MPC" in greeting
    assert conf >= 0.6

    # 2. Embedded & Automation track
    track, name, pdf, greeting, skills, conf = ResumeRouter.resolve_track(
        "嵌入式软件工程师", "负责STM32H7开发与FreeRTOS驱动"
    )
    assert track == "embedded_auto"
    assert "自动化与嵌入式版" in name
    assert "王云鹤_简历_自动化.pdf" in pdf
    assert "STM32H7" in greeting

    # 3. Mechatronics track
    track, name, pdf, greeting, skills, conf = ResumeRouter.resolve_track(
        "机电工程师", "负责EPLAN电气图纸设计与伺服系统选型联调"
    )
    assert track == "mechatronics"
    assert "机电一体化与电气版" in name
    assert "王云鹤_简历_机电.pdf" in pdf

    # 4. Mechanical CFD track
    track, name, pdf, greeting, skills, conf = ResumeRouter.resolve_track(
        "结构仿真工程师", "负责SolidWorks建模与Fluent流固耦合仿真"
    )
    assert track == "mechanical_cfd"
    assert "机械结构与仿真版" in name
    assert "王云鹤_简历_机械.pdf" in pdf
    assert "Fluent" in greeting
