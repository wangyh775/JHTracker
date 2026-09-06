import re
from typing import List, Optional

# 常见岗位类型规则映射
JOB_CATEGORY_RULES = {
    "软件研发类": [
        "软件", "研发", "前端", "后端", "全栈", "开发", "程序员", "java", "python", "c++", "c#", "golang", "go",
        "嵌入式", "测试", "qa", "测试工程师", "it", "信息技术", "运维", "devops", "系统开发", "web", "app", "客户端"
    ],
    "算法/AI类": [
        "算法", "ai", "机器学习", "深度学习", "人工智能", "大模型", "llm", "nlp", "计算机视觉", "cv", "推荐算法",
        "数据分析", "大数据", "数据挖掘", "图像算法", "语音算法", "智能网联", "数据科学"
    ],
    "机械制造类": [
        "机械", "制造", "工艺", "结构", "自动化", "机电", "模具", "流体", "装配", "设备", "热管理", "焊接", "数控", "智能制造"
    ],
    "硬件电子类": [
        "硬件", "电子", "电气", "电路", "pcb", "芯片", "集成电路", "半导体", "fpga", "射频", "通信工程", "光电", "微电子"
    ],
    "营销/销售类": [
        "营销", "销售", "市场", "商务", "客户经理", "渠道", "公关", "拓展", "外贸", "商业化", "海外销售", "销售代表"
    ],
    "职能/HR/财务": [
        "hr", "人力资源", "人事", "行政", "财务", "会计", "出纳", "法务", "审计", "采购", "供应链", "后勤", "资产", "合规"
    ],
    "产品/运营类": [
        "产品经理", "产品专员", "运营", "用户运营", "活动运营", "新媒体", "策划", "交互设计", "ui", "ux", "设计", "视觉"
    ],
    "综合管培类": [
        "管培生", "管培", "储备干部", "管理培训生", "综合管理", "青年人才", "专才计划", "晨星计划", "领航员"
    ]
}

# 噪音批次标签黑名单（完全忽略，绝不进入HITL权重）
IGNORED_BATCH_TAGS = {
    "27秋招", "26秋招", "25秋招", "秋招", "春招", "校园招聘", "校招", "补录", "提前批", "实习",
    "校招正式批", "应届生", "2027", "2026", "2025", "国企", "央企", "外企", "民企", "上市公司", "大厂"
}

def extract_job_categories(title: str, description: Optional[str] = None) -> List[str]:
    """
    根据岗位标题和描述精准提取岗位大类（如 软件研发类、机械制造类、营销/销售类 等）
    """
    text = (title + " " + (description or "")).lower()
    
    # 优先看 ' - 后面' 的岗位部分
    parts = title.split(" - ")
    specific_part = parts[-1].lower() if len(parts) > 1 else ""
    
    matched = []
    # 1. 优先命中 title specific_part
    if specific_part:
        for cat, kws in JOB_CATEGORY_RULES.items():
            if any(kw in specific_part for kw in kws):
                matched.append(cat)
                
    # 2. 若未命中，扫描整体文本
    if not matched:
        for cat, kws in JOB_CATEGORY_RULES.items():
            if any(kw in text for kw in kws):
                matched.append(cat)
                
    return matched or ["综合其他类"]

def extract_primary_city(location: Optional[str]) -> Optional[str]:
    """
    从岗位地点提取主城市（去除省份前缀、行政区等噪音）
    """
    if not location:
        return None
    loc = location.split(",")[0].split("/")[0].split("·")[0].strip()
    loc = re.sub(r"市|区|县$", "", loc)
    if not loc or loc in ["全国", "全国各地", "不限", "远程", "异地"]:
        return None
    # 截取前2~4个汉字（如 北京、上海、深圳、武汉、杭州、乌鲁木齐）
    return loc[:4]
