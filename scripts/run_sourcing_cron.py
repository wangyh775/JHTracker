import sys
import os
import json
import datetime

sys.path.insert(0, r"D:\DJTU\HermesWorkspace\career-tracker")
import mcp_server

def run_sourcing():
    task_id = f"sourcing-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"Starting task: {task_id}")

    # 1. Start trace
    mcp_server.record_agent_trace(
        task_id=task_id,
        agent_name="SourcingAgent",
        event_type="start",
        payload={"action": "init", "timestamp": datetime.datetime.now().isoformat()}
    )

    # 2. Preferences loaded
    mcp_server.record_agent_trace(
        task_id=task_id,
        agent_name="SourcingAgent",
        event_type="preferences_loaded",
        payload={
            "enterprise_preference": "不限",
            "recruitment_type": "校招",
            "target_graduation_year": 2027,
            "job_posted_date_threshold": "2026-07-01",
            "target_domains": ["具身/人形机器人", "3D打印/增材制造", "嵌入式控制算法(STM32/RK3588/MPC/EKF)", "商业航天/军工"]
        }
    )

    # Define verified candidates
    candidates = [
        {
            "company_name": "长光卫星技术股份有限公司",
            "industry": "商业航天/卫星制造",
            "city": "长春",
            "priority": "S",
            "website": "https://www.jl1.cn",
            "source_url": "https://www.wondercv.com/xiaozhao/changguang-satellite-2027-campus-recruitment-12581-509d95",
            "position": "伺服控制工程师（2027届校招）",
            "score": 92,
            "score_reason": "商业航天遥感卫星龙头，伺服控制工程师岗位职责包含永磁同步电机伺服系统与振镜控制建模仿真、伺服控制算法开发、程序编写调试及增材制造研究，高度契合候选人电机与运动控制算法及机械仿真背景。",
            "job_desc": json.dumps({
                "must_have_skills": ["永磁同步电机伺服系统", "伺服控制算法开发", "系统建模与仿真", "嵌入式调试"],
                "nice_to_have": ["振镜控制", "增材制造", "电机参数辨识"],
                "salary_min": 20,
                "salary_max": 27,
                "location": "长春",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-19"
            }, ensure_ascii=False)
        },
        {
            "company_name": "中科本原科技（北京）有限公司",
            "industry": "集成电路/DSP芯片/工业控制",
            "city": "北京/青岛",
            "priority": "A",
            "website": "https://www.fdmtek.com",
            "source_url": "https://www.wondercv.com/xiaozhao/zhongke-benyuan-2027-beijing-qingdao-dsp-12538-450176",
            "position": "电机控制软件工程师（2027届校招）",
            "score": 90,
            "score_reason": "中科院自动化所成果转化企业，自主研发RISC-V架构DSP芯片及工业控制解决方案。电机控制软件工程师岗位专注电机控制算法与嵌入式底层软件开发，与候选人嵌入式控制与算法背景高度对口。",
            "job_desc": json.dumps({
                "must_have_skills": ["C/C++", "DSP/嵌入式软件开发", "电机控制算法(FOC/PID/滤波)", "RISC-V/ARM"],
                "nice_to_have": ["工业控制", "实时系统"],
                "salary_min": 20,
                "salary_max": 32,
                "location": "北京/青岛",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-16"
            }, ensure_ascii=False)
        },
        {
            "company_name": "维泛智能科技（北京）有限公司",
            "industry": "具身智能/芯片与算力",
            "city": "北京/上海/深圳",
            "priority": "S",
            "website": "https://www.vifun.ai",
            "source_url": "https://campus.niuqizp.com/job-vky5zMZMN.html",
            "position": "小脑算法开发工程师 / 底软开发工程师（2027届校招）",
            "score": 93,
            "score_reason": "北大类脑芯片实验室孵化，聚焦机器人原生大小脑融合芯片与底层算力。小脑算法与底软开发岗位负责机器人底层运控算法及软硬件协同部署，与候选人RK3588/STM32分布式架构与先进控制算法深度匹配。",
            "job_desc": json.dumps({
                "must_have_skills": ["机器人小脑运控算法", "C/C++", "Linux嵌入式底软", "软硬件协同优化"],
                "nice_to_have": ["具身智能", "BIGPU/NPU部署"],
                "salary_min": 25,
                "salary_max": 40,
                "location": "北京/上海/深圳",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-08"
            }, ensure_ascii=False)
        },
        {
            "company_name": "星尘智能（Astribot）",
            "industry": "具身智能/人形机器人",
            "city": "深圳",
            "priority": "S",
            "website": "https://www.astribot.com",
            "source_url": "https://www.wondercv.com/xiaozhao/astrirobot-shenzhen-2027-campus-recruitment-11654-5686a6",
            "position": "机器人嵌入式开发工程师 / 运控算法工程师（2027届校招）",
            "score": 95,
            "score_reason": "全球首家实现绳驱人形AI机器人量产企业，全栈自研AI模型-具身OS-绳驱本体。岗位要求极高机电协同、嵌入式实时动作控制与控制算法能力，与候选人控制与机电一体化背景极度契合。",
            "job_desc": json.dumps({
                "must_have_skills": ["C/C++", "机器人运动控制算法", "嵌入式实时控制", "机电系统联调"],
                "nice_to_have": ["绳驱机器人", "具身OS", "MPC/强化学习"],
                "salary_min": 25,
                "salary_max": 45,
                "location": "深圳",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-07-19"
            }, ensure_ascii=False)
        },
        {
            "company_name": "Sharpa机器人",
            "industry": "具身智能/双足人形机器人",
            "city": "北京",
            "priority": "S",
            "website": "https://www.sharparobotics.com",
            "source_url": "https://campus.niuqizp.com/job-vUU5zZ5ML.html",
            "position": "机器人运动控制与嵌入式研发工程师（2027校招提前批）",
            "score": 91,
            "score_reason": "清华系顶尖双足人形机器人初创团队，聚焦高动态运控与高功率密度机电系统。控制与嵌入式研发岗全面覆盖动力学建模、MPC/WBC运控与嵌入式固件开发，技术栈完全契合。",
            "job_desc": json.dumps({
                "must_have_skills": ["动力学建模", "MPC/WBC控制算法", "C/C++", "嵌入式实时系统"],
                "nice_to_have": ["双足人形机器人", "电机驱动调试"],
                "salary_min": 25,
                "salary_max": 40,
                "location": "北京",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-07-25"
            }, ensure_ascii=False)
        }
    ]

    created_apps = []

    for cand in candidates:
        # Check if company exists
        search_res = json.loads(mcp_server.search_companies(query=cand["company_name"]))
        comp_list = search_res.get("companies", [])
        
        comp_id = None
        if comp_list:
            for c in comp_list:
                if c["name"] == cand["company_name"] or cand["company_name"] in c["name"]:
                    comp_id = c["id"]
                    break
        
        if not comp_id:
            create_res = json.loads(mcp_server.create_company(
                name=cand["company_name"],
                industry=cand["industry"],
                city=cand["city"],
                priority=cand["priority"],
                website=cand["website"],
                match_reason=cand["score_reason"],
                score=cand["score"],
                score_reason=cand["score_reason"]
            ))
            comp_id = create_res.get("company_id")
            print(f"Created company {cand['company_name']} -> ID {comp_id}")
        else:
            # update score if needed
            mcp_server.update_company_score(company_id=comp_id, score=cand["score"], reason=cand["score_reason"])
            print(f"Found existing company {cand['company_name']} -> ID {comp_id}")
        
        # Check deduplication on applications
        conn = mcp_server.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, position, status, source_url FROM applications WHERE company_id = ? AND status IN ('Pending Approval', '待审批', '待投递')", (comp_id,))
        existing_apps = cursor.fetchall()
        
        dup = False
        for a in existing_apps:
            if cand["position"] in a["position"] or a["position"] in cand["position"]:
                dup = True
                break
                
        if dup:
            print(f"Skipping duplicate proposal for {cand['company_name']}: {cand['position']}")
            mcp_server.record_agent_trace(
                task_id=task_id,
                agent_name="SourcingAgent",
                event_type="skip",
                payload={"skipped": True, "reason": "duplicate_proposal", "company": cand["company_name"], "position": cand["position"]}
            )
            continue
            
        # Create application
        app_res = json.loads(mcp_server.create_application(
            company_id=comp_id,
            position=cand["position"],
            job_desc=cand["job_desc"],
            url=cand["source_url"],
            source_url=cand["source_url"],
            channel="Agent 全网自动搜寻 (2027届秋招/提前批)",
            match_score=cand["score"],
            agent_reason=cand["score_reason"],
            agent_task_id=task_id,
            status="Pending Approval",
            source_platform="网络多源公开校招"
        ))
        print(f"Created application for {cand['company_name']} -> App ID {app_res.get('application_id')}")
        created_apps.append({
            "company": cand["company_name"],
            "position": cand["position"],
            "score": cand["score"],
            "url": cand["source_url"]
        })

    # Finish trace
    mcp_server.record_agent_trace(
        task_id=task_id,
        agent_name="SourcingAgent",
        event_type="finish",
        status="completed",
        payload={
            "created_applications": len(created_apps),
            "proposals": created_apps,
            "timestamp": datetime.datetime.now().isoformat()
        }
    )

    print(f"Task completed successfully. Total new applications created: {len(created_apps)}")

if __name__ == "__main__":
    run_sourcing()
