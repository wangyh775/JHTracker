import pytest
import os
import shutil
import tempfile
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.recommendation_service import RecommendationService
from src.models import JobItem

@pytest.mark.asyncio
async def test_recommendation_and_hitl_loop():
    temp_dir = tempfile.mkdtemp()
    try:
        pub_db = os.path.join(temp_dir, "pub.db")
        user_db = os.path.join(temp_dir, "user.db")

        from src.db import init_public_db, init_user_db
        await init_public_db(pub_db)
        await init_user_db(user_db)

        job_repo = JobRepository(pub_db)
        user_repo = UserRepository(user_db)
        rec_service = RecommendationService(job_repo, user_repo)

        # 插入测试岗位
        await job_repo.insert_job(JobItem(
            id="job-1",
            title="Python 后端开发工程师",
            company="未来科技",
            location="北京",
            industry="人工智能",
            type_tags=["上市", "外企"],
            publish_date="2026-09-01",
            description="精通 Python 与 FastAPI 微服务"
        ))

        await job_repo.insert_job(JobItem(
            id="job-2",
            title="Java 软件工程师",
            company="某某外包",
            location="外地",
            industry="外包服务",
            type_tags=["外包"],
            publish_date="2026-09-01",
            description="负责传统业务维护"
        ))

        # 1. 查询推荐
        recs = await rec_service.get_recommendations(min_score=0.1)
        assert len(recs) == 2

        # 2. 拒绝 job-2 (勾选行业原因：不看外包行业)
        await rec_service.record_feedback("job-2", "REJECT", ["行业不符: 不看外包"])

        # 3. 验证 P0 定向衰减：仅 industry 被抑制，软件研发类 category 绝对没有被误伤扣减
        weights = await user_repo.get_feature_weights()
        assert weights.get("industry:外包服务") is not None
        assert weights.get("industry:外包服务") <= 0.80
        assert weights.get("category:软件研发类") is None  # 验证没有连坐误伤

        # 3.1 测试定向拒绝职能方向：当用户明确拒绝职能时才扣减 category
        await rec_service.record_feedback("job-2", "REJECT", ["岗位职能方向不符"])
        weights_after_cat = await user_repo.get_feature_weights()
        assert weights_after_cat.get("category:软件研发类") is not None
        assert weights_after_cat.get("category:软件研发类") <= 0.80

        # 4. 再次获取推荐，job-2 不应再出现
        recs_after = await rec_service.get_recommendations(min_score=0.1)
        assert len(recs_after) == 1
        assert recs_after[0]["job"]["id"] == "job-1"

        # 5. 接受 job-1，验证自动进入 applications 待投递面板
        await rec_service.record_feedback("job-1", "ACCEPT")
        apps = await user_repo.list_applications(status="PENDING_APPLY")
        assert len(apps) == 1
        assert apps[0].company == "未来科技"

        # 6. 验证频控与去重：
        # 6.1 插入未来科技的更多岗位测试上限 (已有1个待投递，再插入3个)
        for i in range(2, 5):
            await job_repo.insert_job(JobItem(
                id=f"job-future-{i}",
                title=f"Python 开发工程师 {i}",
                company="未来科技",
                location="北京",
                industry="人工智能",
                type_tags=["互联网"],
                publish_date="2026-09-01",
                description="Python 开发"
            ))
        
        # 此时未来科技待投递区有 1 个，限制 max_jobs_per_company=3，推荐列表最多只能再给 2 个
        recs_cap = await rec_service.get_recommendations(min_score=0.1, max_jobs_per_company=3)
        future_recs = [r for r in recs_cap if r["job"]["company"] == "未来科技"]
        assert len(future_recs) <= 2

        # 6.2 将未来科技在待投递区补足到 3 个
        from src.models import ApplicationItem
        await user_repo.create_or_update_application(ApplicationItem(
            id="app-future-b",
            job_id="job-future-b",
            company="未来科技",
            title="岗位B",
            status="PENDING_APPLY"
        ))
        await user_repo.create_or_update_application(ApplicationItem(
            id="app-future-c",
            job_id="job-future-c",
            company="未来科技",
            title="岗位C",
            status="PENDING_APPLY"
        ))
        
        # 此时待投递已达 3 个，未来科技应当被完全频控，不再推荐
        recs_capped = await rec_service.get_recommendations(min_score=0.1, max_jobs_per_company=3)
        assert not any(r["job"]["company"] == "未来科技" for r in recs_capped)

        # 6.3 验证已投递企业拉黑：将某企业状态变更为 APPLIED
        await job_repo.insert_job(JobItem(
            id="job-applied-1",
            title="结构工程师",
            company="拓竹科技",
            location="深圳",
            industry="智能制造",
            type_tags=["硬件"],
            publish_date="2026-09-01",
            description="3D打印机结构设计"
        ))
        await user_repo.create_or_update_application(ApplicationItem(
            id="app-applied-tz",
            job_id="job-applied-1",
            company="拓竹科技",
            title="结构设计",
            status="APPLIED"
        ))
        recs_after_apply = await rec_service.get_recommendations(min_score=0.1)
        assert not any(r["job"]["company"] == "拓竹科技" for r in recs_after_apply)

        # 7. 验证关键词矩阵对推荐打分与负向词一票否决的驱动
        from src.models import ResumeItem, KeywordMatrix, KeywordMatrixCategories, KeywordItem
        matrix_data = KeywordMatrix(
            categories=KeywordMatrixCategories(
                core=[KeywordItem(keyword="FastAPI", weight=2.5, enabled=True)],
                domain=[KeywordItem(keyword="具身智能", weight=2.0, enabled=True)],
                base=[KeywordItem(keyword="Docker", weight=1.0, enabled=True)],
                negative=[KeywordItem(keyword="外包", weight=0.1, enabled=True)]
            ),
            updated_by="USER_MANUAL"
        )
        test_resume = ResumeItem(
            id="res-matrix-1",
            title="具身智能算法简历",
            is_default=True,
            keywords_matrix=matrix_data
        )
        await user_repo.save_resume(test_resume)

        # 插入具身智能与外包岗位
        await job_repo.insert_job(JobItem(
            id="job-embodied-1",
            title="具身智能算法工程师",
            company="智元机器人",
            location="上海",
            industry="人工智能",
            type_tags=["独角兽"],
            publish_date="2026-09-02",
            description="负责具身大模型与 FastAPI 接口开发"
        ))
        await job_repo.insert_job(JobItem(
            id="job-outsourcing-1",
            title="外包支持工程师",
            company="新外包",
            location="上海",
            industry="IT服务",
            type_tags=["外包"],
            publish_date="2026-09-02",
            description="驻场外包服务支持"
        ))

        recs_matrix = await rec_service.get_recommendations(resume_id="res-matrix-1", min_score=0.1)
        embodied_rec = next((r for r in recs_matrix if r["job"]["id"] == "job-embodied-1"), None)
        outsourcing_rec = next((r for r in recs_matrix if r["job"]["id"] == "job-outsourcing-1"), None)

        assert embodied_rec is not None
        assert embodied_rec["score"] >= 0.70  # 核心词与领域词全中，得分应当显著高
        assert "命中核心技能" in embodied_rec["reason"]

        # 验证矩阵中的关键词已 100% 自动注册到 HITL feature_weights 字典中
        weights = await user_repo.get_feature_weights()
        assert "skill:FastAPI" in weights
        assert "domain:具身智能" in weights
        assert "skill:Docker" in weights

        if outsourcing_rec:
            # 标题含外包 negative 词，得分应被压制到极低
            assert outsourcing_rec["score"] <= 0.20
            assert outsourcing_rec.get("negative_hit") == "外包"

    finally:
        shutil.rmtree(temp_dir)
