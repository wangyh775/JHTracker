"""Execute direct SQL updates and app creation using sqlite3 directly"""
import sqlite3
import json

db_path = r"D:/DJTU/HermesWorkspace/career-tracker/data/tracker.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

task_id = "cron_midnight_review_20260822"
agent_name = "MidnightCompanyReviewAgent"

# 1. Update tasks table
cur.execute("SELECT id FROM agent_tasks WHERE task_id = ?", (task_id,))
row = cur.fetchone()
if row:
    task_pk = row['id']
    cur.execute("UPDATE agent_tasks SET status = 'running', agent_name = ? WHERE id = ?", (agent_name, task_pk))
else:
    cur.execute("INSERT INTO agent_tasks (task_id, agent_name, status, created_at) VALUES (?, ?, 'running', datetime('now'))", (task_id, agent_name))
    task_pk = cur.lastrowid
conn.commit()

# Start event
cur.execute("INSERT INTO agent_events (task_id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))",
            (task_pk, "start", json.dumps({
                "timestamp": "2026-08-22T00:00:00+08:00",
                "rotation_batch": [775, 776, 777, 779, 783],
                "message": "启动库内 S/A 级重点企业夜间深度复盘 (00:00 轮询任务)"
            }, ensure_ascii=False)))
conn.commit()

reviews = [
    {
        "company_id": 775,
        "name": "杭州宇树科技有限公司",
        "new_score": 97,
        "score_reason": "【2026-08-22 夜间深度复盘】S级重点企业（宇树科技）。2027届校园招聘持续推进，官网热招“嵌入式软件开发工程师（BLDC/PMSM电机控制与机电系统）”、“深度强化学习算法工程师”及“机器人感知与运控”。与候选人STM32H7/Linux底层驱动开发、电机FOC矢量控制及MPC高精度控制算法实战经验极度契合，保持97分高分。",
        "new_position": {
            "position": "嵌入式软件开发工程师（电机控制与驱动）",
            "job_desc": "1. 负责无刷电机（BLDC）、永磁同步电机（PMSM）控制程序开发；\n2. 机电控制系统开发，嵌入式软件开发，相关传感器、结构驱动开发；\n3. 电机相关可靠性测试、研发及生产用测试台/治具开发；\n4. 要求精通C/C++、ARM/STM32/Linux嵌入式驱动开发，具备电机FOC/矢量控制与实时控制算法基础。",
            "url": "https://www.unitree.com/mobile/position",
            "source_url": "https://www.unitree.com/mobile/position",
            "channel": "企业官网校招",
            "match_score": 97,
            "agent_reason": "宇树科技2027届官网热招核心研发岗。岗位要求BLDC/PMSM电机控制程序开发与机电控制系统开发，与候选人STM32H7/Linux底层驱动开发、电机FOC矢量控制及MPC高精度控制算法实战经验极度契合。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 776,
        "name": "广州中望龙腾软件股份有限公司",
        "new_score": 94,
        "score_reason": "【2026-08-22 夜间深度复盘】A级重点工业软件龙头（中望软件）。2027届秋招全面启动（发布时间2026-07-23/07-29，广州/武汉/上海），官网热招“AI应用开发工程师（工业场景Agent与CAx/C++）”、“CAE研发工程师”与“ZW3D研发工程师”。候选人机械工程硕士、SolidWorks+CFD流热耦合仿真、OrcaSlicer源码级二次开发及Langgraph多智能体AI Agent全栈极度契合，上调至94分。",
        "new_position": {
            "position": "AI应用开发工程师（工业Agent与CAx）（2027届）",
            "job_desc": "1. 负责工业场景下AI Agent智能体的设计、开发与多智能体工作流重构；\n2. 参与大模型与三维CAD/CAM/CAE工业软件的深度结合与算法落地；\n3. 负责三维几何造型、切片与工艺优化相关C++模块开发；\n4. 要求硕士及以上学历，机械工程/计算机/力学背景，熟悉Python、C++，有AI Agent或开源CAx二次开发经验优先。",
            "url": "https://www.zwsoft.cn/job/campus",
            "source_url": "https://www.zwsoft.cn/job/campus",
            "channel": "企业官网校招",
            "match_score": 94,
            "agent_reason": "中望软件2027届共性技术研究院核心AI+工业软件岗位（prefer_company正向偏好加成）。候选人具备机械工程硕士学历，曾对OrcaSlicer源码二次开发并深度集成Langgraph多智能体AI Agent重构切片工作流，技能与研发方向完美契合。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 777,
        "name": "北京国望光学科技有限公司",
        "new_score": 93,
        "score_reason": "【2026-08-22 夜间深度复盘】A级重点企业（北京国望光学）。IC光刻机曝光光学系统战略国企，2027届校招全面推进，热招超精密系统仿真工程师（光/力/热协同设计）、微环境控制工程师（流场/热控仿真）与超精密机械类岗位。候选人机械硕士、SolidWorks设计、CFD热流固耦合仿真及精密温控算法深度契合，提供北京落户，上调至93分。",
        "new_position": {
            "position": "机械环境控制工程师（2027届校招）",
            "job_desc": "1. 负责超精密光学系统环境热控、流场与精密机械结构协同设计与仿真分析；\n2. 负责热流固耦合CFD仿真建模、微环境温度状态估计与精密温控方案制定；\n3. 参与超精密机电系统联调与环境控制指标验证；\n4. 要求机械工程/热能与动力/控制工程硕士及以上学历，精通SolidWorks与CFD仿真，具备精密温控/控制算法背景。",
            "url": "https://job.tju.edu.cn/company/index/sxid/126/id/1921.html",
            "source_url": "https://job.tju.edu.cn/company/index/sxid/126/id/1921.html",
            "channel": "校园招聘",
            "match_score": 93,
            "agent_reason": "国望光学2027届校招核心战略研发岗（解决北京户口+prefer_company正向偏好）。候选人机械工程硕士背景，精通SolidWorks设计，拥有PEEK高温喷头流热耦合CFD仿真及MPC/EKF精密温控实战经历，且符合北京落户政策与正向偏好规则加成。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 779,
        "name": "深圳格见半导体有限公司",
        "new_score": 91,
        "score_reason": "【2026-08-22 夜间深度复盘】A级重点企业（格见半导体）。国产工业级实时控制DSP芯片领军企业，2027届校招全面开启（面向2027届硕博/本科），热招嵌入式软件开发工程师（负责RTOS内核组件、Bootloader及芯片外设驱动），产品覆盖具身机器人与高精度运动控制。候选人STM32H7/Linux系统开发、电机驱动及FOC运控经验极度契合，上调至91分。",
        "new_position": {
            "position": "嵌入式软件开发工程师（RTOS/芯片外设驱动-2027届）",
            "job_desc": "1. 负责自主DSP芯片平台RTOS操作系统核心组件设计与开发；\n2. 负责Bootloader、Flash算法及芯片外设驱动（PWM/ADC/SPI/CAN/UART）的设计与优化；\n3. 协助进行电机控制（FOC）与实时控制算法在DSP芯片上的移植与调试；\n4. 要求自动化/电子/计算机相关专业，精通C/C++，熟悉ARM Cortex-M/DSP架构及嵌入式实时系统。",
            "url": "https://www.gejian-semi.com/about/careers",
            "source_url": "https://www.gejian-semi.com/about/careers",
            "channel": "企业官网校招",
            "match_score": 91,
            "agent_reason": "格见半导体2027届校招核心嵌入式研发岗（prefer_company正向偏好加成）。候选人具备STM32H7与Linux底层外设驱动开发能力，熟悉RTOS与通信协议，具备电机控制算法落地经验，与DSP驱动与控制生态开发高度契合。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    },
    {
        "company_id": 783,
        "name": "深圳市普渡科技股份有限公司",
        "new_score": 95,
        "score_reason": "【2026-08-22 夜间深度复盘】A级商用服务与具身机器人龙头（普渡机器人）。2027届秋招全面推进（深圳/成都），全面布局“专用+类人形+人形”全形态机器人与“具身智能一脑多形”架构，热招具身Agent开发工程师、运动控制算法工程师及嵌入式系统工程师。候选人RK3588/STM32分布式架构、MPC/EKF控制算法及Langgraph Agent切片优化经历高度匹配，上调至95分。",
        "new_position": {
            "position": "具身Agent开发工程师（2027届校招）",
            "job_desc": "1. 负责商用/具身智能机器人通用Agent智能体工作流设计与落地；\n2. 负责大模型驱动的任务规划、多智能体协同与业务场景决策逻辑实现；\n3. 参与端侧系统与上层Agent交互接口的开发与调优；\n4. 要求计算机/自动化/机械工程相关专业硕士，熟悉Python/C++，具备AI Agent/Langgraph或机器人控制系统开发经验。",
            "url": "https://career.nankai.edu.cn/correcruit/content/id/116156.html",
            "source_url": "https://career.nankai.edu.cn/correcruit/content/id/116156.html",
            "channel": "校园招聘",
            "match_score": 95,
            "agent_reason": "普渡机器人2027届校招核心前沿研发岗。普渡全面发力“具身智能一脑多形”，候选人具备Langgraph多智能体AI Agent开发经验，且拥有Linux+RK3588分布式控制系统全栈实践，与具身Agent开发高度匹配。",
            "resume_id": 1,
            "form_type": "open_question",
            "source_platform": "official"
        }
    }
]

execution_summary = []
STAGED_STATUS_LIST = ['Pending Approval', '待审批', '待投递', '准备投递']

for item in reviews:
    cid = item["company_id"]
    cname = item["name"]
    new_score = item["new_score"]
    score_reason = item["score_reason"]
    pos_data = item["new_position"]

    # 1. Update company score
    cur.execute("UPDATE companies SET score = ?, score_reason = ? WHERE id = ?", (new_score, score_reason, cid))
    conn.commit()

    # 2. Check deduplication
    norm_pos = pos_data["position"].strip()
    placeholders = ','.join(['?'] * len(STAGED_STATUS_LIST))
    sql = f"""
        SELECT id, company_id, position, status, url, match_score, agent_reason, agent_task_id, source_url, resume_id, form_type, source_platform
        FROM applications
        WHERE company_id = ? AND LOWER(TRIM(position)) = LOWER(?) AND status IN ({placeholders})
        LIMIT 1
    """
    cur.execute(sql, (cid, norm_pos, *STAGED_STATUS_LIST))
    existing = cur.fetchone()

    app_created = False
    app_id = None

    if existing:
        app_id = existing['id']
        app_created = False
    else:
        cur.execute("""
            INSERT INTO applications (
                company_id, position, job_desc, url, channel, status, 
                match_score, agent_reason, agent_task_id, source_url, 
                resume_id, form_type, source_platform, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'Pending Approval', ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            cid, pos_data["position"], pos_data["job_desc"], pos_data["url"],
            pos_data["channel"], pos_data["match_score"], pos_data["agent_reason"],
            task_id, pos_data["source_url"], pos_data["resume_id"],
            pos_data.get("form_type", "open_question"), pos_data.get("source_platform", "official")
        ))
        conn.commit()
        app_id = cur.lastrowid
        app_created = True

    # Record trace event
    cur.execute(
        "INSERT INTO agent_events (task_id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))",
        (task_pk, "company_review_completed", json.dumps({
            "company_id": cid,
            "company_name": cname,
            "new_score": new_score,
            "score_reason": score_reason,
            "application": {
                "id": app_id,
                "created": app_created,
                "position": pos_data["position"],
                "match_score": pos_data["match_score"]
            }
        }, ensure_ascii=False))
    )
    conn.commit()

    execution_summary.append({
        "company_id": cid,
        "name": cname,
        "new_score": new_score,
        "position": pos_data["position"],
        "match_score": pos_data["match_score"],
        "source_url": pos_data["source_url"],
        "app_created": app_created,
        "app_id": app_id
    })

# Complete trace
cur.execute("UPDATE agent_tasks SET status = 'success' WHERE id = ?", (task_pk,))
cur.execute(
    "INSERT INTO agent_events (task_id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))",
    (task_pk, "complete", json.dumps({
        "summary": "成功完成 5 家轮询企业 (宇树科技、中望软件、国望光学、格见半导体、普渡科技) 的 2027 届校招深度复盘，更新评分并新增/确认投递提案。",
        "completed_targets": execution_summary
    }, ensure_ascii=False))
)
conn.commit()

with open(r"D:/DJTU/HermesWorkspace/career-tracker/scripts/midnight_review_20260822_result.json", "w", encoding="utf-8") as f:
    json.dump(execution_summary, f, ensure_ascii=False, indent=2)

conn.close()
