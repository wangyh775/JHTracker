import os
from typing import Dict, Any, Tuple, List

class ResumeRouter:
    """4 轨简历与 HR 打招呼话术智能路由合成器

    4 轨细分：
    1. control (控制算法): MPC/EKF/状态空间/运动控制/论文/专利
    2. embedded_auto (自动化与嵌入式): STM32H7/RK3588/Linux/Klipper/PLC/驱动
    3. mechatronics (机电一体化与电气): EPLAN/ECAD/电气柜/抗干扰/传感器选型/综合
    4. mechanical_cfd (机械结构与仿真): SolidWorks/CoreXY/CFD/Fluent/热流固耦合/有限元
    """

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    RESUMES_DIR = os.path.join(BASE_DIR, "data", "resumes")

    TRACKS: Dict[str, Dict[str, Any]] = {
        "control": {
            "name": "控制算法版",
            "pdf_name": "王云鹤_简历_控制.pdf",
            "keywords": [
                "控制算法", "算法工程师", "运动控制", "mpc", "ekf", "卡尔曼滤波", "状态空间",
                "动力学", "轨迹规划", "自适应控制", "鲁棒控制", "最优控制", "matlab", "simulink",
                "控制理论", "观测器", "论文", "专利", "控制系统"
            ],
            "skills": ["MPC模型预测控制", "EKF状态滤波", "状态空间动力学建模", "Simulink数字孪生仿真", "EI在审论文/发明专利"],
            "greeting_template": (
                "您好！我是大连交通大学机械工程硕士（2027届）王云鹤。主攻控制理论与高精度运动控制算法，"
                "具备MPC模型预测控制、EKF状态滤波及多轴联动轨迹规划经验，已发表1篇EI在审论文并申请1项发明专利。"
                "看到贵司正在招聘 {position}，我的控制算法研究与项目实践高度匹配，期待能与您深入交流！"
            )
        },
        "embedded_auto": {
            "name": "自动化与嵌入式版",
            "pdf_name": "王云鹤_简历_自动化.pdf",
            "keywords": [
                "嵌入式", "自动化", "单片机", "stm32", "rk3588", "arm", "linux", "c/c++",
                "freertos", "rt-thread", "klipper", "固件", "底层驱动", "can", "rs485", "uart",
                "spi", "i2c", "plc", "上位机", "步进电机驱动", "foc"
            ],
            "skills": ["STM32H7/RK3588分布式主控架构", "Linux/FreeRTOS嵌入式开发", "Klipper固件深度定制", "工业总线(CAN/RS485)", "机器人国奖"],
            "greeting_template": (
                "您好！我是大连交通大学机械工程硕士（2027届）王云鹤。精通STM32H7与RK3588异构分布式主控架构，"
                "具备Linux/FreeRTOS底层驱动、Klipper固件二次开发及工业总线(CAN/RS485)通信实战经验，曾获全国机器人创意大赛一等奖。"
                "看到贵司正在招聘 {position}，希望能向您自荐并呈递简历！"
            )
        },
        "mechatronics": {
            "name": "机电一体化与电气版",
            "pdf_name": "王云鹤_简历_机电.pdf",
            "keywords": [
                "机电", "机电一体化", "电气", "电气工程", "eplan", "ecad", "电气原理图", "接线图",
                "抗干扰", "电气柜", "元器件选型", "传感器", "伺服系统", "步进系统", "配电",
                "仪器仪表", "系统集成", "整机联调", "测试工程师"
            ],
            "skills": ["EPLAN电气原理图/柜体规划", "500mm整机机电联调", "工业传感器与伺服选型", "EMC抗干扰设计", "国家一等奖团队领队"],
            "greeting_template": (
                "您好！我是大连交通大学机械工程硕士（2027届）王云鹤。主修机电系统集成与电气工程设计，"
                "独立负责过500mm大幅面工业级设备的EPLAN电气原理图设计、工业抗震机柜布局及传感器/伺服选型联调（获国家一等奖）。"
                "看到贵司招聘 {position}，我的综合工程实践能力能快速上手工作，期待能与您沟通！"
            )
        },
        "mechanical_cfd": {
            "name": "机械结构与仿真版",
            "pdf_name": "王云鹤_简历_机械.pdf",
            "keywords": [
                "机械", "结构", "机械设计", "结构设计", "solidworks", "creo", "ug", "catia",
                "热设计", "热仿真", "cfd", "fluent", "ansys", "有限元", "fea", "热流耦合",
                "结构强度", "钣金", "corexy", "3d打印", "腔体设计", "热流场"
            ],
            "skills": ["500mm工业级CoreXY结构设计", "SolidWorks精密建模与工程图", "ANSYS Fluent热流固耦合仿真", "钣金/腔体热管理", "EI论文/发明专利"],
            "greeting_template": (
                "您好！我是大连交通大学机械工程硕士（2027届）王云鹤。主攻复杂机械系统结构设计与多物理场耦合仿真，"
                "独立完成500mm高温恒温FDM整机结构设计（CoreXY架构），并使用ANSYS Fluent完成腔体热流场与热变形仿真（1篇EI，1项发明专利）。"
                "看到贵司正在招聘 {position}，非常希望能加入贵司研发团队！"
            )
        }
    }

    @classmethod
    def resolve_track(cls, job_title: str, job_description: str = "") -> Tuple[str, str, str, str, List[str], float]:
        """根据岗位标题和描述综合判定所属 4 轨

        Returns:
            (track_key, track_name, resume_pdf_path, greeting_copy, highlight_skills, confidence_score)
        """
        text = f"{job_title} {job_description}".lower()

        scores: Dict[str, int] = {}
        for key, info in cls.TRACKS.items():
            # 标题权重更高 (x3)
            title_hits = sum(1 for kw in info["keywords"] if kw in job_title.lower())
            desc_hits = sum(1 for kw in info["keywords"] if kw in text)
            scores[key] = title_hits * 3 + desc_hits

        # 选出最高分
        sorted_tracks = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_track, top_score = sorted_tracks[0]

        if top_score == 0:
            # 默认兜底：机电一体化通用轨道
            top_track = "mechatronics"
            confidence = 0.5
        else:
            confidence = min(1.0, 0.6 + (top_score / 15.0) * 0.4)

        track_info = cls.TRACKS[top_track]
        resume_pdf_path = os.path.join(cls.RESUMES_DIR, track_info["pdf_name"])
        greeting = track_info["greeting_template"].format(position=job_title)

        return (
            top_track,
            track_info["name"],
            resume_pdf_path,
            greeting,
            track_info["skills"],
            round(confidence, 2)
        )
