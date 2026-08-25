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
            "target_domains": ["具身/人形机器人", "半导体装备/精密制造", "嵌入式/控制算法/时空智能", "低轨卫星/AI+时空", "智能装备/电气工程"]
        }
    )

    candidates = [
        {
            "company_name": "上海极洞科技有限公司",
            "industry": "商业航天/卫星互联网/AI时空智能",
            "city": "上海",
            "priority": "S",
            "website": "https://campus.niuqizp.com/schedulenote-hrmUYNZa5-1.html",
            "source_url": "https://www.wondercv.com/xiaozhao/jiedong-tech-shanghai-2027-campus-recruitment-12900-c0e033",
            "position": "机器人端侧嵌入式软件工程师 / 规控算法工程师（2027届校招）",
            "score": 93,
            "score_reason": "G60卫星互联网创新中心生态企业，专注于卫星+AI双引擎驱动的时空智能技术。岗位涵盖机器人端侧嵌入式底软驱动、ROS/ROS2平台自主导航规控算法调试与多源融合定位，深度契合候选人嵌入式底层架构及控制算法背景。",
            "job_desc": json.dumps({
                "must_have_skills": ["C/C++", "ROS/ROS2", "嵌入式底软驱动开发", "自主导航规控算法"],
                "nice_to_have": ["低轨卫星增强定位", "多源传感器融合", "SLAM"],
                "salary_min": 22,
                "salary_max": 35,
                "location": "上海",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-23"
            }, ensure_ascii=False)
        },
        {
            "company_name": "杭州曦诺未来科技有限公司",
            "industry": "具身智能/机器人灵巧手与操控",
            "city": "杭州/深圳",
            "priority": "S",
            "website": "https://www.wondercv.com/xiaozhao/x-gravity-fellows-motion-control-algorithm-hangzhou-12699-8c3646",
            "source_url": "https://www.wondercv.com/xiaozhao/x-gravity-fellows-motion-control-algorithm-hangzhou-12699-8c3646",
            "position": "运动控制算法工程师（X-Gravity Fellows高能计划 / 2027届校招）",
            "score": 95,
            "score_reason": "顶尖具身智能灵巧操控独角兽，专注机器人灵巧手与高动态运动控制。运动控制算法工程师岗位要求精通多轴运控、动力学建模仿真与先进控制算法，与候选人MPC/EKF先进控制理论与嵌入式落地能力极度对口。",
            "job_desc": json.dumps({
                "must_have_skills": ["机器人运动控制算法", "C/C++", "动力学建模与仿真", "现代控制理论(MPC/滤波)"],
                "nice_to_have": ["机器人灵巧手操控", "力控算法", "强化学习运控"],
                "salary_min": 25,
                "salary_max": 45,
                "location": "杭州/深圳",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-20"
            }, ensure_ascii=False)
        },
        {
            "company_name": "上海上纬启元机器人科技有限公司",
            "industry": "消费级具身智能/人形机器人",
            "city": "上海/北京",
            "priority": "S",
            "website": "https://www.wondercv.com/xiaozhao/primebot-2027-campus-shanghai-12793-757c39",
            "source_url": "https://www.wondercv.com/xiaozhao/primebot-2027-campus-shanghai-12793-757c39",
            "position": "机器人运控与嵌入式系统工程师 / 机器人结构工程师（2027届校招）",
            "score": 94,
            "score_reason": "上纬新材旗下消费级具身智能品牌，业界最大规模350+人校招，研发启元Q1全身力控人形机器人。技术族涵盖机器人运控、嵌入式系统及本体结构设计，与候选人机械结构、电机力控与嵌入式开发背景完全一致。",
            "job_desc": json.dumps({
                "must_have_skills": ["机器人全身力控/运控算法", "嵌入式软硬件协同", "C/C++", "SolidWorks/机械结构设计"],
                "nice_to_have": ["人形机器人样机调试", "消费级机器人产品化", "多模态感知"],
                "salary_min": 22,
                "salary_max": 38,
                "location": "上海/北京",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-21"
            }, ensure_ascii=False)
        },
        {
            "company_name": "拓荆科技股份有限公司",
            "industry": "半导体装备/薄膜沉积与键合设备",
            "city": "沈阳/上海/青岛",
            "priority": "A",
            "website": "https://www.piotech.cn",
            "source_url": "https://www.wondercv.com/xiaozhao/piotech-2027-campus-recruitment-12789-c78634",
            "position": "电气工程师 / 多轴精密运动控制工程师（2027届校招）",
            "score": 91,
            "score_reason": "科创板上市半导体薄膜沉积与三维集成先进键合设备龙头。电气工程师岗位负责芯片键合设备电气控制方案设计、多轴精密运动控制开发与调试、EDA电气原理图设计，与候选人EPLAN/ECAD电气设计与控制背景高度对口。",
            "job_desc": json.dumps({
                "must_have_skills": ["电气系统设计(EPLAN/EDA)", "多轴精密运动控制", "PLC/嵌入式控制", "电气元器件选型"],
                "nice_to_have": ["半导体设备研发", "精密机械电子联调", "CFD/流热仿真"],
                "salary_min": 18,
                "salary_max": 30,
                "location": "沈阳/上海/青岛",
                "recruitment_type": "校招",
                "target_graduation_year": 2027,
                "job_posted_date": "2026-08-21"
            }, ensure_ascii=False)
        }
    ]

    created_apps = []
    skipped_apps = []

    for cand in candidates:
        name = cand["company_name"]
        pos = cand["position"]
        print(f"\nProcessing: {name} - {pos}")

        # Search company
        search_res = mcp_server.search_companies(query=name)
        if isinstance(search_res, str):
            search_res = json.loads(search_res)
        matched_cos = search_res if isinstance(search_res, list) else search_res.get("companies", [])
        
        company_id = None
        if matched_cos:
            for co in matched_cos:
                if co["name"] == name or name in co["name"] or co["name"] in name:
                    company_id = co["id"]
                    print(f"  Found existing company: ID {company_id} ({co['name']})")
                    break

        if not company_id:
            create_res = mcp_server.create_company(
                name=name,
                industry=cand["industry"],
                city=cand["city"],
                priority=cand["priority"],
                website=cand["website"],
                match_reason=cand["score_reason"],
                score=cand["score"],
                score_reason=cand["score_reason"]
            )
            if isinstance(create_res, str):
                create_res = json.loads(create_res)
            print(f"  Created company: {create_res}")
            if isinstance(create_res, dict) and create_res.get("created"):
                company_id = create_res.get("company")["id"]
            elif isinstance(create_res, dict) and "company" in create_res:
                company_id = create_res["company"]["id"]
            else:
                # fallback search
                s_res = mcp_server.search_companies(query=name)
                if isinstance(s_res, str):
                    s_res = json.loads(s_res)
                s_cos = s_res if isinstance(s_res, list) else s_res.get("companies", [])
                if s_cos:
                    company_id = s_cos[0]["id"]

        if not company_id:
            print(f"  Failed to get/create company ID for {name}")
            continue

        # Check existing applications for deduplication
        existing_apps = mcp_server.list_applications(company_id=company_id)
        if isinstance(existing_apps, str):
            existing_apps = json.loads(existing_apps)
        is_dup = False
        app_list = existing_apps if isinstance(existing_apps, list) else existing_apps.get("applications", [])
        for app in app_list:
            if app.get("position") == pos or pos in app.get("position", ""):
                is_dup = True
                break

        if is_dup:
            print(f"  Duplicate application found. Skipping.")
            mcp_server.record_agent_trace(
                task_id=task_id,
                agent_name="SourcingAgent",
                event_type="trace",
                payload={"skipped": True, "reason": "duplicate_proposal", "company": name, "position": pos}
            )
            skipped_apps.append({"company": name, "position": pos})
            continue

        # Evaluate and score
        mcp_server.update_company_score(
            company_id=company_id,
            score=cand["score"],
            reason=cand["score_reason"]
        )

        # Create application in Pending Approval
        app_res = mcp_server.create_application(
            company_id=company_id,
            position=pos,
            status="Pending Approval",
            source_url=cand["source_url"],
            url=cand["source_url"],
            match_score=cand["score"],
            agent_reason=cand["score_reason"],
            agent_task_id=task_id,
            job_desc=cand["job_desc"],
            source_platform="wondercv"
        )
        print(f"  Created application: {app_res}")
        created_apps.append({
            "company": name,
            "position": pos,
            "city": cand["city"],
            "score": cand["score"],
            "url": cand["source_url"]
        })

    # Record completion trace
    mcp_server.record_agent_trace(
        task_id=task_id,
        agent_name="SourcingAgent",
        event_type="finish",
        status="completed",
        payload={
            "created_applications_count": len(created_apps),
            "created_applications": created_apps,
            "skipped_applications": skipped_apps
        }
    )

    print("\nSourcing completed successfully.")
    return created_apps

if __name__ == "__main__":
    res = run_sourcing()
    print("Result summary:", json.dumps(res, ensure_ascii=False, indent=2))
