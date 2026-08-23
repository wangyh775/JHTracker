import sys
import os
import json
import sqlite3

# Set working directory to career-tracker
sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")

from mcp_server import (
    update_company_score,
    create_application,
    record_agent_trace,
    get_user_preferences
)

task_id = "midnight-review-20260821-000000"
agent_name = "MidnightCompanyReviewAgent"

# 1. Record start event
res_start = record_agent_trace(
    task_id=task_id,
    agent_name=agent_name,
    event_type="start",
    payload={
        "timestamp": "2026-08-21T00:00:00+08:00",
        "rotation_batch": [775, 776, 777, 779, 783],
        "message": "启动库内 S/A 级重点企业夜间深度复盘 (00:00 轮询任务)"
    },
    status="running"
)
print("Trace start:", res_start)

# Candidate targets
reviews = [
    {
        "company_id": 775,
        "name": "杭州宇树科技有限公司",
        "new_score": 97,
        "score_reason": "【2026-08-21 夜间深度复盘】S级重点企业。2027届校园招聘全面推进，官网热招“嵌入式软件开发工程师（BLDC/PMSM电机控制/机电控制系统）”、“AI算法工程师（机器人大模型/控制）”与“机器人感知与运控”。与候选人电机矢量控制、STM32/RK3588及MPC/EKF控制算法高度契合，保持97分高分。",
        "new_position": {
            "position": "嵌入式软件开发工程师（电机控制与驱动）",
            "job_desc": "1. 负责无刷电机（BLDC）、永磁同步电机（PMSM）控制程序开发；\n2. 机电控制系统开发，嵌入式软件开发，相关传感器、结构驱动开发；\n3. 电机相关可靠性测试、研发及测试台/治具开发；\n4. 要求精通C/C++、ARM/STM32/Linux嵌入式驱动开发，具备电机FOC/矢量控制与实时控制算法基础。",
            "url": "https://www.unitree.com/cn/position",
            "source_url": "https://www.unitree.com/cn/position",
            "channel": "企业官网校招",
            "match_score": 97,
            "agent_reason": "宇树科技2027届官网热招核心研发岗。岗位要求BLDC/PMSM电机控制程序开发与机电控制系统开发，与候选人STM32H7/Linux底层驱动开发、电机FOC矢量控制及MPC高精度控制算法实战经验100%契合。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 776,
        "name": "广州中望龙腾软件股份有限公司",
        "new_score": 94,
        "score_reason": "【2026-08-21 夜间深度复盘】A级重点工业软件龙头。2027届秋招全面启动（广州/武汉/上海），官网热招“AI应用开发工程师（工业场景Agent与CAx/C++）”、“CAE研发工程师”与“ZW3D研发工程师”。候选人机械工程硕士、SolidWorks+CFD流热耦合仿真、OrcaSlicer源码级二次开发及Langgraph多智能体AI Agent全栈极度契合，上调至94分。",
        "new_position": {
            "position": "AI应用开发工程师（工业Agent与CAx）（2027届）",
            "job_desc": "1. 负责工业场景下AI Agent智能体的设计、开发与多智能体工作流重构；\n2. 参与大模型与三维CAD/CAM/CAE工业软件的深度结合与算法落地；\n3. 负责三维几何造型、切片与工艺优化相关C++模块开发；\n4. 要求硕士及以上学历，机械工程/计算机/力学背景，熟悉Python、C++，有AI Agent或开源CAx二次开发经验优先。",
            "url": "https://www.zwsoft.cn/job/campus",
            "source_url": "https://www.zwsoft.cn/job/campus",
            "channel": "企业官网校招",
            "match_score": 94,
            "agent_reason": "中望软件2027届共性技术研究院核心AI+工业软件岗位。候选人具备机械工程硕士学历，曾对OrcaSlicer源码二次开发并深度集成Langgraph多智能体AI Agent重构切片工作流，技能与研发方向完美契合。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 777,
        "name": "北京国望光学科技有限公司",
        "new_score": 93,
        "score_reason": "【2026-08-21 夜间深度复盘】A级重点企业（北京国望光学）。IC光刻机曝光光学系统战略国企，2027届校招全面推进，热招机械机电类、机械环境控制类与软件算法类岗位。候选人机械硕士、SolidWorks设计、CFD热流固耦合仿真及精密温控算法深度契合，提供北京落户，上调至93分。",
        "new_position": {
            "position": "机械环境控制工程师（2027届校招）",
            "job_desc": "1. 负责超精密光学系统环境热控、流场与精密机械结构协同设计与仿真分析；\n2. 负责热流固耦合CFD仿真建模、温度状态估计与精密温控方案制定；\n3. 参与超精密机电系统联调与环境控制指标验证；\n4. 要求机械工程/热能与动力/控制工程硕士及以上学历，精通SolidWorks与CFD仿真，具备温控算法背景。",
            "url": "https://campus.niuqizp.com/job-vmy5zzttn.html",
            "source_url": "https://campus.niuqizp.com/job-vmy5zzttn.html",
            "channel": "校园招聘",
            "match_score": 93,
            "agent_reason": "国望光学2027届校招核心战略研发岗。候选人机械工程硕士背景，精通SolidWorks设计，拥有PEEK高温喷头流热耦合CFD仿真及MPC/EKF精密温控实战经历，且符合北京落户政策与正向偏好规则加成。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 779,
        "name": "深圳格见半导体有限公司",
        "new_score": 91,
        "score_reason": "【2026-08-21 夜间深度复盘】A级重点企业。国产工业级实时控制DSP芯片领军企业，2027校招热招嵌入式软件开发工程师（负责RTOS内核组件、Bootloader及芯片外设驱动），产品覆盖具身机器人与高精度运动控制。候选人STM32H7/Linux系统开发、电机驱动及FOC运控经验极度契合，上调至91分。",
        "new_position": {
            "position": "嵌入式软件开发工程师（RTOS/芯片外设驱动）",
            "job_desc": "1. 负责自主DSP芯片平台RTOS操作系统核心组件设计与开发；\n2. 负责Bootloader、Flash算法及芯片外设驱动（PWM/ADC/SPI/CAN/UART）的设计与优化；\n3. 协助进行电机控制（FOC）与实时控制算法在DSP芯片上的移植与调试；\n4. 要求自动化/电子/计算机相关专业，精通C/C++，熟悉ARM Cortex-M/DSP架构及嵌入式实时系统。",
            "url": "https://www.gejian-semi.com/about/careers",
            "source_url": "https://www.gejian-semi.com/about/careers",
            "channel": "企业官网校招",
            "match_score": 91,
            "agent_reason": "格见半导体2027届校招核心嵌入式研发岗。候选人具备STM32H7与Linux底层外设驱动开发能力，熟悉RTOS与通信协议，具备电机控制算法落地经验，与DSP驱动与控制生态开发高度契合。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 783,
        "name": "深圳市普渡科技股份有限公司",
        "new_score": 95,
        "score_reason": "【2026-08-21 夜间深度复盘】A级商用服务与具身机器人龙头。2027届校招与实习项目火热进行中（深圳/成都），开放运动控制算法、通用具身Agent开发及嵌入式系统工程师全栈岗位。候选人RK3588/STM32分布式架构、MPC/EKF控制算法及Langgraph Agent切片优化经历高度匹配，上调至95分。",
        "new_position": {
            "position": "具身Agent开发工程师（2027届校招）",
            "job_desc": "1. 负责商用/具身智能机器人通用Agent智能体工作流设计与落地；\n2. 负责大模型驱动的任务规划、多智能体协同与业务场景决策逻辑实现；\n3. 参与端侧系统与上层Agent交互接口的开发与调优；\n4. 要求计算机/自动化/机械工程相关专业硕士，熟悉Python/C++，具备AI Agent/Langgraph或机器人控制系统开发经验。",
            "url": "https://career.nankai.edu.cn/correcruit/content/id/116156.html",
            "source_url": "https://career.nankai.edu.cn/correcruit/content/id/116156.html",
            "channel": "校园招聘",
            "match_score": 95,
            "agent_reason": "普渡机器人2027届校招核心前沿研发岗。候选人具备Langgraph多智能体AI Agent开发经验，且拥有Linux+RK3588分布式控制系统全栈实践，与具身Agent开发高度匹配。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    }
]

created_apps = []
score_updates = []

for r in reviews:
    cid = r["company_id"]
    score = r["new_score"]
    reason = r["score_reason"]
    
    # 1. Update company score
    res_score = update_company_score(cid, score, reason)
    print(f"Update score company {cid}:", res_score)
    score_updates.append({"company_id": cid, "name": r["name"], "score": score, "result": json.loads(res_score)})
    
    # 2. Create application proposal
    np = r["new_position"]
    res_app = create_application(
        company_id=cid,
        position=np["position"],
        job_desc=np["job_desc"],
        url=np["url"],
        channel=np["channel"],
        match_score=np["match_score"],
        agent_reason=np["agent_reason"],
        agent_task_id=task_id,
        source_url=np["source_url"],
        resume_id=np["resume_id"],
        status="Pending Approval",
        form_type=np["form_type"],
        source_platform=np["source_platform"]
    )
    print(f"Create app for company {cid}:", res_app)
    created_apps.append({"company_id": cid, "name": r["name"], "result": json.loads(res_app)})

# 3. Record agent trace finish
res_finish = record_agent_trace(
    task_id=task_id,
    agent_name=agent_name,
    event_type="complete",
    payload={
        "summary": "成功完成 5 家轮询企业（宇树科技、中望软件、国望光学、格见半导体、普渡科技）的 2027 届校招深度复盘，更新企业评分与理由，并生成 5 条有效投递建议提案。",
        "reviewed_companies": score_updates,
        "application_proposals": created_apps,
        "timestamp": "2026-08-21T00:05:00+08:00"
    },
    status="success"
)
print("Trace finish:", res_finish)

out_summary = {
    "task_id": task_id,
    "status": "success",
    "score_updates": score_updates,
    "created_apps": created_apps
}

with open(r"D:/DJTU/HermesWorkspace/career-tracker/scripts/review_execution_summary.json", "w", encoding="utf-8") as f:
    json.dump(out_summary, f, ensure_ascii=False, indent=2)

print("Execution completed successfully.")
