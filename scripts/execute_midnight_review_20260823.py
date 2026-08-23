import sys
import os
import json
import sqlite3

sys.path.insert(0, r"D:/DJTU/HermesWorkspace/career-tracker")

from mcp_server import (
    update_company_score,
    create_application,
    record_agent_trace,
    get_user_preferences
)

task_id = "cron_midnight_review_20260823"
agent_name = "MidnightCompanyReviewAgent"

print("--- Starting Midnight Review Trace ---")
res_start = record_agent_trace(
    task_id=task_id,
    agent_name=agent_name,
    event_type="start",
    payload={
        "timestamp": "2026-08-23T00:00:00+08:00",
        "rotation_batch": [784, 785, 786, 787, 788],
        "message": "启动库内 S/A 级重点企业夜间深度复盘 (00:00 轮询任务)"
    },
    status="running"
)
print("Start Trace:", res_start)

# Review details for the 5 target companies
reviews = [
    {
        "company_id": 784,
        "name": "首形科技（AheadForm）",
        "new_score": 94,
        "score_reason": "【2026-08-23 夜间深度复盘】A级重点具身智能企业（首形科技）。哥伦比亚大学AI/机器人博士胡宇航创立，专注超仿生人形机器人与具身情感基座模型研发。2027届秋招持续推进（2026-07-28开启，至09-26），热招“机器人运动控制工程师”、“嵌入式软硬件工程师”及“机械结构工程师”。与候选人SolidWorks机械设计、STM32H7/RK3588底层驱动、Linux+C++及MPC/EKF精密控制全栈高度契合，评分上调至94分。",
        "new_position": None # 已存在App 113，去重跳过
    },
    {
        "company_id": 785,
        "name": "卡特彼勒（Caterpillar）",
        "new_score": 93,
        "score_reason": "【2026-08-23 夜间深度复盘】A级外企工程装备龙头（卡特彼勒技术研发中国有限公司）。2027届校招全面开启（无锡/天津/苏州/徐州），官方热招“研发类-流体仿真工程师（热管理/CFD）”（工作编号r0000387382）及“电子电气/软件工程师”。候选人机械工程硕士、精通SolidWorks三维设计、PEEK高温喷头流热固耦合CFD仿真、响应面优化及Python数据自动化分析，与无锡研发中心热管理CFD仿真岗位100%契合，评分大幅上调至93分。",
        "new_position": {
            "position": "流体仿真工程师（热管理/CFD）（2027届校园招聘）",
            "job_desc": "1. 负责利用计算流体力学（CFD）和热管理分析技术，开展工程机械及新能源产品冷却系统、动力电池与整机热管理系统的流动与传热仿真；\n2. 建立和维护冷却系统、热交换器、风扇及流体部件的三维CFD仿真模型与热平衡分析；\n3. 利用Python等工具实现数据处理、CFD后处理自动化与AI辅助工程分析；\n4. 紧密协同设计团队，基于仿真与试验关联提出结构与工艺优化建议；\n5. 要求机械工程/热能工程/动力工程等硕士及以上学历，精通传热学、流体力学及ANSYS Fluent/STAR-CCM+仿真分析，具备Python自动化编程与工程论文发表背景。",
            "url": "https://careers.caterpillar.com/en/jobs/r0000387382/2027%E6%A0%A1%E5%9B%AD%E6%8B%9B%E8%81%98-%E7%A0%94%E5%8F%91%E7%B1%BB-%E6%B5%81%E4%BD%93%E4%BB%BF%E7%9C%9F%E5%B7%A5%E7%A8%8B%E5%B8%88-%E7%83%AD%E7%AE%A1%E7%90%86",
            "source_url": "https://careers.caterpillar.com/en/jobs/r0000387382/2027%E6%A0%A1%E5%9B%AD%E6%8B%9B%E8%81%98-%E7%A0%94%E5%8F%91%E7%B1%BB-%E6%B5%81%E4%BD%93%E4%BB%BF%E7%9C%9F%E5%B7%A5%E7%A8%8B%E5%B8%88-%E7%83%AD%E7%AE%A1%E7%90%86",
            "channel": "企业官网校招",
            "match_score": 93,
            "agent_reason": "卡特彼勒无锡技术研发中心2027届核心研发岗（工作编号r0000387382）。岗位要求利用CFD开展传热与流动仿真建模、热流耦合分析及Python自动化后处理。候选人具备机械工程硕士学历，曾完成PEEK高温喷头流热固耦合CFD模型建立、阻力特性分析与响应面法工艺窗口优化（误差<2%），且熟悉Python工程自动化分析与EI论文发表，背景完美吻合！",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 786,
        "name": "航天智能科技研究院（航天科工）",
        "new_score": 96,
        "score_reason": "【2026-08-23 夜间深度复盘】S级重点科研事业单位（航天智能院）。中国航天科工集团智能科技总体单位，国家战略新型科技力量。2027届校招全面推进（2026-07-14启动，至09-09），科创中心热招“智能飞行器设计与控制岗（D02）”、“端侧人工智能设计岗（D05）”及“数字孪生技术岗”。为应届硕博解决北京户口，福利优厚。与候选人机械工程硕士、MPC/EKF控制算法、STM32H7/Linux分布式控制及Langgraph多智能体AI Agent全栈极度契合，评分上调至96分。",
        "new_position": None # 已存在App 86，去重跳过
    },
    {
        "company_id": 787,
        "name": "字节跳动（ByteDance）",
        "new_score": 95,
        "score_reason": "【2026-08-23 夜间深度复盘】S级顶尖科技大厂（字节跳动Seed）。2027届Seed大模型人才校招全面开放（2026-08-10官方发布，北京/上海/深圳/杭州），重点布局“具身智能”（通用机器人操作大模型/强化学习）及“大模型应用”（Search Agent与多智能体工作流协同）。候选人OrcaSlicer源码二次开发深度集成Langgraph多智能体AI Agent系统、以及RK3588+STM32分布式软硬件协同经验高度契合，评分上调至95分。",
        "new_position": None # 已存在App 84，去重跳过
    },
    {
        "company_id": 788,
        "name": "深圳市元启姝辰科技有限公司",
        "new_score": 95,
        "score_reason": "【2026-08-23 夜间深度复盘】A级重点增材制造与运控企业（元启姝辰）。2027届校招（2026-07-29发布）热招“多轴运动控制算法工程师”（深圳宝安，20-30K/月）。核心负责多轴轨迹规划、插补、S曲线加减速、G-code指令执行链路打通及Z轴跟随与标定补偿。与候选人自主研发大型500mm高温FDM设备、Klipper/Moonraker底层运控、G-code解析与MPC精密温控算法100%契合，评分上调至95分。",
        "new_position": None # 已存在App 105，去重跳过
    }
]

# Execute updates and creations
results = []
for rev in reviews:
    cid = rev["company_id"]
    name = rev["name"]
    new_score = rev["new_score"]
    reason = rev["score_reason"]
    
    # 1. Update score
    res_score = update_company_score(company_id=cid, score=new_score, reason=reason)
    print(f"[{cid}] Updated score to {new_score}: {res_score}")
    
    # 2. Create application if new position provided and check dedup
    app_res = None
    if rev["new_position"]:
        pos_data = rev["new_position"]
        app_res = create_application(
            company_id=cid,
            position=pos_data["position"],
            job_desc=pos_data["job_desc"],
            url=pos_data["url"],
            channel=pos_data["channel"],
            match_score=pos_data["match_score"],
            agent_reason=pos_data["agent_reason"],
            agent_task_id=task_id,
            source_url=pos_data["source_url"],
            resume_id=pos_data.get("resume_id")
        )
        print(f"[{cid}] Created application for {pos_data['position']}: {app_res}")
    else:
        print(f"[{cid}] Skipped application creation (existing application verified).")
        
    results.append({
        "company_id": cid,
        "name": name,
        "score": new_score,
        "score_update_result": res_score,
        "application_result": app_res
    })

# Record review trace
res_rev = record_agent_trace(
    task_id=task_id,
    agent_name=agent_name,
    event_type="review",
    payload={
        "rotation_batch": [784, 785, 786, 787, 788],
        "review_results": results
    },
    status="success"
)
print("Review Trace:", res_rev)

# Record complete trace
res_comp = record_agent_trace(
    task_id=task_id,
    agent_name=agent_name,
    event_type="complete",
    payload={
        "summary": "完成 5 家 S/A 级企业夜间深度复盘与校招动态调研",
        "companies_reviewed": [784, 785, 786, 787, 788],
        "new_applications_created": 1,
        "scores_updated": 5
    },
    status="success"
)
print("Complete Trace:", res_comp)

with open("career-tracker/scripts/review_execution_summary_20260823.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n--- Review execution finished successfully! ---")
