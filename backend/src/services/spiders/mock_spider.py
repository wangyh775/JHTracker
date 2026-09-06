import uuid
from datetime import datetime, timedelta
from typing import List
from src.services.spiders.base_spider import BaseJobSpider
from src.models import JobItem

class MockJobSpider(BaseJobSpider):
    """
    内置 Mock 岗位数据源适配器，用于离线环境测试与快速演示冷启动
    """
    async def fetch_jobs(self, since_date: str) -> List[JobItem]:
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        last_week = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        two_months_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        mock_raw_data = [
            {
                "title": "大模型算法工程师",
                "company": "智谱探索科技",
                "location": "北京",
                "industry": "人工智能",
                "type_tags": ["Python", "PyTorch", "LLM", "RAG", "Agent"],
                "batch": "2027届秋招提前批",
                "education_req": "硕士及以上",
                "target_grad_year": ["2026", "2027"],
                "salary_range": "35k-55k·16薪",
                "publish_date": today_str,
                "deadline": "2026-11-30",
                "detail_url": "https://campus.zhipu.example.com/job/001",
                "referral_code": "ZP_AGENT_2026",
                "description": "负责大语言模型微调、Agent 工作流开发与知识库 RAG 系统架构落地，要求熟悉 PyTorch、FastAPI 与主流分布式训练框架。",
                "source_site": "MOCK",
                "popular_level": 5
            },
            {
                "title": "Python 全栈开发专家",
                "company": "字节跳动",
                "location": "上海",
                "industry": "互联网",
                "type_tags": ["Python", "FastAPI", "React", "TypeScript", "Docker"],
                "batch": "2026届校园招聘",
                "education_req": "本科及以上",
                "target_grad_year": ["2026"],
                "salary_range": "25k-40k·15薪",
                "publish_date": yesterday,
                "deadline": "2026-10-31",
                "detail_url": "https://job.bytedance.example.com/job/102",
                "referral_code": "BYTEDANCE_REF",
                "description": "负责内部开发者工具与敏捷平台核心业务系统研发，技术栈覆盖 Python、FastAPI、React 及微服务治理。",
                "source_site": "MOCK",
                "popular_level": 5
            },
            {
                "title": "具身智能具身控制研发工程师",
                "company": "宇树科技",
                "location": "杭州",
                "industry": "智能硬件/机器人",
                "type_tags": ["C++", "Python", "ROS2", "强化学习"],
                "batch": "2026届全球春招",
                "education_req": "硕士及以上",
                "target_grad_year": ["2026"],
                "salary_range": "30k-45k·14薪",
                "publish_date": last_week,
                "deadline": "2026-12-31",
                "detail_url": "https://unitree.example.com/job/204",
                "referral_code": "",
                "description": "负责四足/双足人形机器人运动规划与步态强化学习算法落地，熟悉 ROS2、C++ 与 Isaac Gym 仿真。",
                "source_site": "MOCK",
                "popular_level": 4
            },
            {
                "title": "推荐搜索算法工程师",
                "company": "美团",
                "location": "北京",
                "industry": "本地生活",
                "type_tags": ["Python", "C++", "推荐算法", "深度学习"],
                "batch": "2026校招",
                "education_req": "硕士及以上",
                "target_grad_year": ["2026"],
                "salary_range": "28k-45k·15薪",
                "publish_date": two_months_ago,
                "deadline": "2026-09-30",
                "detail_url": "https://zhaopin.meituan.example.com/job/301",
                "referral_code": "MT_HERMES",
                "description": "负责美团核心到店、到家业务的召回、排序模型演进与多模态推荐特征挖掘优化。",
                "source_site": "MOCK",
                "popular_level": 4
            }
        ]

        jobs: List[JobItem] = []
        for item in mock_raw_data:
            if item["publish_date"] >= since_date:
                job_id = f"job_mock_{hash(item['company'] + item['title']) & 0xFFFFFFFF:08x}"
                jobs.append(JobItem(
                    id=job_id,
                    **item
                ))
        return jobs
