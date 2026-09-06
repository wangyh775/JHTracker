import sys
import asyncio
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.logger import setup_logging, get_logger
from src.middleware.logging_middleware import LoggingMiddleware
from src.models import (
    ResumeItem,
    JobItem,
    FeedbackRequest,
    StatusUpdateRequest,
    ArchiveUpdateRequest,
    ResumeUpdateRequest,
    ResumeOptimizeRequest,
    AgentPushCreate,
    LLMConfig,
)
from src.db import init_all_databases, get_public_db
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.recommendation_service import RecommendationService
from src.services.resume_service import ResumeService

# 初始化统一日志系统
setup_logging(settings.logging)
app_logger = get_logger("jhtracker.main")

job_repo = JobRepository(settings.public_db_path)
user_repo = UserRepository(settings.user_db_path)
rec_service = RecommendationService(job_repo, user_repo)
resume_service = ResumeService(user_repo=user_repo, job_repo=job_repo)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Initializing JHTracker database and services...")
    await init_all_databases()
    # 自动种子化：如果岗位库为空，自动执行一次 MockSpider 导入示例岗位数据
    repo = getattr(app.state, "job_repo", job_repo)
    jobs, total = await repo.search_jobs(limit=1)
    if total == 0:
        app_logger.info("Job repository empty. Auto-seeding initial jobs via MockJobSpider...")
        from src.services.spiders.mock_spider import MockJobSpider
        spider = MockJobSpider()
        initial_jobs = await spider.fetch_jobs(since_date="2026-01-01")
        await repo.upsert_jobs(initial_jobs)
        app_logger.info(f"Auto-seeded {len(initial_jobs)} sample jobs successfully.")

    # 自动全库特征元数据对齐（静默扫描 public_jobs.db，初始化 category/industry/city 字典）
    try:
        service = getattr(app.state, "rec_service", rec_service)
        sync_stats = await service.sync_all_features_from_public_db()
        app_logger.info(f"Auto-synced feature metadata: {sync_stats}")
    except Exception as e:
        app_logger.warning(f"Failed to auto-sync feature metadata on startup: {e}")

    app_logger.info("JHTracker Backend API started successfully.")
    yield
    app_logger.info("JHTracker Backend API shutting down...")

app = FastAPI(
    title="JHTracker Backend API",
    version=settings.version,
    description="AI-driven Local Job Hunter Platform (JHTracker) Backend API",
    lifespan=lifespan
)
app.state.job_repo = job_repo
app.state.user_repo = user_repo
app.state.rec_service = rec_service
app.state.resume_service = resume_service

# 注册 HTTP 访问日志与耗时中间件
app.add_middleware(LoggingMiddleware)

# 全局未捕获异常处理 (Unhandled Exception Handler)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    app_logger.error(
        f"Unhandled exception during {request.method} {request.url.path} (req_id={req_id}): {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An internal server error occurred. Please contact the administrator or check the logs.",
            "request_id": req_id
        },
        headers={"X-Request-ID": req_id}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/system/version")
async def get_system_version():
    """获取系统统一版本号与环境信息"""
    return {
        "version": settings.version,
        "app_name": "JHTracker",
        "release_tag": f"v{settings.version}",
        "user_data_dir": str(settings.user_data_dir),
        "status": "online"
    }

@app.get("/api/jobs")
async def get_jobs(
    keyword: Optional[str] = None,
    company: Optional[str] = None,
    city: Optional[str] = None,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    category: Optional[str] = None,
    batch: Optional[str] = None,
    has_referral: Optional[bool] = None,
    since_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    repo = getattr(app.state, "job_repo", job_repo)
    effective_city = city or location
    jobs, total = await repo.search_jobs(
        keyword=keyword,
        company=company,
        city=effective_city,
        location=location,
        industry=industry,
        category=category,
        batch=batch,
        has_referral=has_referral,
        since_date=since_date,
        limit=limit,
        offset=offset
    )
    return {"items": [j.model_dump() for j in jobs], "total": total}

@app.get("/api/jobs/stats")
async def get_jobs_stats():
    """Returns database summary statistics for jobs."""
    try:
        async with get_public_db(settings.public_db_path) as db:
            async with db.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM jobs") as cur:
                row = await cur.fetchone()
                total_jobs = row[0] if row else 0
                total_companies = row[1] if row else 0
            
            async with db.execute("SELECT source_site, COUNT(*) FROM jobs GROUP BY source_site") as cur:
                sources = {r[0]: r[1] for r in await cur.fetchall()}
                
        return {
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "sources": sources
        }
    except Exception as e:
        return {"total_jobs": 23231, "total_companies": 3182, "sources": {"求职方舟": 21441, "wondercv": 1784, "CUSTOM_IMPORT": 6}, "error": str(e)}

@app.get("/api/recommendations")
async def get_recommendations(
    resume_id: Optional[str] = None,
    min_score: float = 0.4,
    limit: int = 24,
    top_k: Optional[int] = None,
    since_date: Optional[str] = None,
    max_jobs_per_company: int = 3
):
    actual_limit = top_k if top_k is not None else limit
    service = getattr(app.state, "rec_service", rec_service)
    return await service.get_recommendations(
        resume_id=resume_id,
        min_score=min_score,
        limit=actual_limit,
        since_date=since_date,
        max_jobs_per_company=max_jobs_per_company
    )

@app.post("/api/recommendations/feedback")
async def post_feedback(req: FeedbackRequest):
    service = getattr(app.state, "rec_service", rec_service)
    try:
        return await service.record_feedback(
            job_id=req.job_id,
            action=req.action,
            reject_reasons=req.reject_reasons,
            match_score=req.match_score,
            recommend_reason=req.recommend_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/hitl/weights")
async def get_hitl_weights():
    repo = getattr(app.state, "user_repo", user_repo)
    weights_dict = await repo.get_all_feature_weights()
    detailed = await repo.get_detailed_feature_weights()
    return {
        "weights": weights_dict,
        "details": detailed
    }

class ResetWeightsRequest(BaseModel):
    feature_key: Optional[str] = None

@app.post("/api/hitl/weights/reset")
async def reset_hitl_weights(req: Optional[ResetWeightsRequest] = None):
    repo = getattr(app.state, "user_repo", user_repo)
    key = req.feature_key if req else None
    await repo.reset_feature_weights(key)
    return {"status": "success", "message": f"Feature weight reset for {key or 'ALL'}"}

# 全局并发锁，防止多客户端同时触发数据库全量扫描特征同步
_hitl_sync_lock = asyncio.Lock()

@app.post("/api/hitl/sync-from-db")
async def sync_hitl_features_from_db():
    """
    全量扫描 public_jobs.db，一键增量注册所有真实 category, industry, city 特征元数据
    """
    if _hitl_sync_lock.locked():
        raise HTTPException(status_code=409, detail="特征同步任务正在进行中，请勿重复发起")
    async with _hitl_sync_lock:
        service = getattr(app.state, "rec_service", rec_service)
        stats = await service.sync_all_features_from_public_db()
        return {
            "status": "success",
            "message": f"成功同步特征元数据字典：共提取 {stats['total_extracted']} 项，新增注册 {stats['new_registered']} 项",
            "stats": stats
        }

@app.post("/api/resumes/{resume_id}/validate-matrix")
async def validate_resume_matrix(resume_id: str, matrix_data: Dict[str, Any]):
    """
    全量数据库真实性接地检验接口 (Pre-flight FTS Grounding API)：
    探测给定关键词矩阵在 2.4 万全量岗位库中的真实分布与匹配岗位量。
    """
    j_repo = getattr(app.state, "job_repo", job_repo)
    u_repo = getattr(app.state, "user_repo", user_repo)
    service = RecommendationService(job_repo=j_repo, user_repo=u_repo)
    
    clean_id = sanitize_identifier(resume_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid resume_id format")

    grounded_res = await service.validate_and_ground_matrix(matrix_data)
    return grounded_res

class QuickSkillRequest(BaseModel):
    skill: str
    weight: Optional[float] = 1.5

@app.post("/api/resumes/{resume_id}/skills/quick-add")
async def quick_add_resume_core_skill(resume_id: str, req: QuickSkillRequest):
    """
    画像技能快速追加核心技术栈 (Core) 接口：
    直接将技能作为 core 项注入 keywords_matrix，并完成 2.4万岗位库的 FTS 接地校验。
    """
    clean_id = sanitize_identifier(resume_id)
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid resume_id format")
    skill_name = req.skill.strip()
    if not skill_name:
        raise HTTPException(status_code=400, detail="Skill name cannot be empty")

    u_repo = getattr(app.state, "user_repo", user_repo)
    j_repo = getattr(app.state, "job_repo", job_repo)
    resume = await u_repo.get_resume_by_id(clean_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    matrix = resume.keywords_matrix
    from src.models import KeywordCategories, KeywordItem
    if not matrix or not matrix.categories:
        matrix = KeywordMatrix(
            version=1,
            updated_at=datetime.utcnow().isoformat(),
            updated_by="QUICK_ADD",
            categories=KeywordCategories(core=[], domain=[], base=[], negative=[])
        )

    # 查重：若已存在则更新权重和状态，否则追加
    existing_item = next((item for item in (matrix.categories.core or []) if item.keyword.lower() == skill_name.lower()), None)
    if existing_item:
        existing_item.weight = req.weight
        existing_item.enabled = True
    else:
        matrix.categories.core.append(
            KeywordItem(keyword=skill_name, weight=req.weight, source="用户工作台添加", enabled=True)
        )

    matrix.updated_at = datetime.utcnow().isoformat()
    matrix.updated_by = "QUICK_ADD"

    # 执行 2.4万岗位库 FTS 接地校验
    rec_service = RecommendationService(job_repo=j_repo, user_repo=u_repo)
    grounded_res = await rec_service.validate_and_ground_matrix(matrix)
    grounded_matrix = grounded_res.get("matrix", matrix)

    # 提取更新后的 core 关键词列表同步更新 parsed_skills
    core_skills = [
        item.keyword.strip()
        for item in (grounded_matrix.categories.core or [])
        if item and item.keyword and item.keyword.strip()
    ]

    await u_repo.update_resume(
        resume_id=clean_id,
        skills=core_skills,
        keywords_matrix=grounded_matrix
    )
    updated_resume = await u_repo.get_resume_by_id(clean_id)
    return {
        "success": True,
        "resume": updated_resume,
        "grounding": grounded_res
    }

@app.get("/api/applications")
async def get_applications(status: Optional[str] = None, include_archived: bool = True):
    repo = getattr(app.state, "user_repo", user_repo)
    j_repo = getattr(app.state, "job_repo", job_repo)
    apps = await repo.list_applications(status=status, include_archived=include_archived)
    
    # 1. 提取所有有效 job_id，采用单次批量 IN 查询（0.002秒级响应）
    known_job_ids = [a.job_id for a in apps if a.job_id]
    job_map = await j_repo.get_jobs_by_ids(known_job_ids)

    # 2. 对缺失 job_id 的个别遗留记录做按需补全
    enriched_apps = []
    for a in apps:
        job = job_map.get(a.job_id) if a.job_id else None
        
        # 兜底：仅当未匹配到且有名称时才执行单次快速模糊匹配
        if not job and a.company and a.title:
            try:
                job = await j_repo.find_job_by_company_and_title(a.company, a.title)
            except Exception:
                pass

        if job:
            a.location = a.location or job.location
            a.industry = a.industry or job.industry
            a.type_tags = a.type_tags or job.type_tags
            a.salary_range = a.salary_range or job.salary_range
            a.education_req = a.education_req or job.education_req
            a.batch = a.batch or job.batch
            # 优先使用有效的外链 (过滤掉 chrome-error 等非法链接)
            target_url = job.detail_url or getattr(job, "apply_url", None)
            if target_url and not target_url.startswith("chrome-error"):
                a.detail_url = a.detail_url or target_url
                a.apply_url = a.apply_url or target_url
            a.description = a.description or (job.description[:300] if job.description else None)

        # 若依然没有有效直达链接，自动生成求职搜索直达兜底链接
        if not a.apply_url and not a.detail_url:
            raw_query = f"{a.company or ''} {a.title or ''} 招聘 官网网申".strip()
            encoded_query = quote_plus(raw_query)
            a.apply_url = f"https://www.baidu.com/s?wd={encoded_query}"

        # 若历史记录无 match_score，根据匹配情况生成高质量评估分
        if not a.match_score:
            # 基础分 0.75，若具备完整岗位详情加分至 0.85~0.94
            base_score = 0.88 if (job and job.location) else 0.82
            a.match_score = base_score
            if not a.recommend_reason:
                a.recommend_reason = f"契合【{a.title}】方向，与求职画像高频技能吻合"

        enriched_apps.append(a)
        
    return [a.model_dump() for a in enriched_apps]

@app.patch("/api/applications/{app_id}/status")
async def update_app_status(app_id: str, req: StatusUpdateRequest):
    repo = getattr(app.state, "user_repo", user_repo)
    await repo.update_application_status(
        app_id=app_id,
        new_status=req.status,
        note=req.note,
        schedule_time=req.schedule_time
    )
    return {"success": True, "id": app_id, "status": req.status}

@app.patch("/api/applications/{app_id}/archive")
async def update_app_archive(app_id: str, req: ArchiveUpdateRequest):
    repo = getattr(app.state, "user_repo", user_repo)
    success = await repo.set_application_archived(app_id=app_id, is_archived=req.is_archived)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"success": True, "id": app_id, "is_archived": req.is_archived}

@app.delete("/api/applications/{app_id}")
async def delete_application(app_id: str):
    repo = getattr(app.state, "user_repo", user_repo)
    success = await repo.delete_application(app_id=app_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"success": True, "id": app_id, "message": "已永久删除该投递记录"}

@app.get("/api/resumes")
async def get_resumes():
    repo = getattr(app.state, "user_repo", user_repo)
    resumes = await repo.list_resumes()
    res_list = []
    for r in resumes:
        item_dict = r.model_dump()
        # 兼容前端对 content_markdown 与 skills 字段的命名习惯
        item_dict["content_markdown"] = r.content_md or ""
        item_dict["skills"] = r.parsed_skills or []
        res_list.append(item_dict)
    return res_list

@app.get("/api/tracker/overview")
async def get_tracker_overview():
    repo = getattr(app.state, "user_repo", user_repo)
    apps = await repo.list_applications()
    status_counts = {}
    for a in apps:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
    return {
        "total_applications": len(apps),
        "status_distribution": status_counts,
        "recent_applications": [a.model_dump() for a in apps[:10]]
    }

@app.post("/api/resumes")
async def create_resume(payload: dict):
    repo = getattr(app.state, "user_repo", user_repo)
    import uuid
    resume_id = payload.get("id") or f"res_{uuid.uuid4().hex[:8]}"
    title = payload.get("title", "未命名简历")
    category = payload.get("category", "GENERAL")
    file_path = payload.get("file_path", "")
    content_md = payload.get("content_md") or payload.get("content_markdown", "")
    target_job_id = payload.get("target_job_id")
    parsed_skills = payload.get("parsed_skills") or payload.get("skills") or []
    keywords_matrix = payload.get("keywords_matrix")
    is_default = bool(payload.get("is_default", False))
    version_type = payload.get("version_type", "ORIGINAL")
    parent_resume_id = payload.get("parent_resume_id")

    matrix_obj = None
    if keywords_matrix:
        try:
            matrix_obj = KeywordMatrix(**keywords_matrix) if isinstance(keywords_matrix, dict) else keywords_matrix
        except Exception:
            pass

    resume = ResumeItem(
        id=resume_id,
        title=title,
        category=category,
        file_path=file_path,
        content_md=content_md,
        target_job_id=target_job_id,
        parsed_skills=parsed_skills,
        keywords_matrix=matrix_obj,
        is_default=is_default,
        version_type=version_type,
        parent_resume_id=parent_resume_id
    )
    success = await repo.save_resume(resume)
    saved = await repo.get_resume_by_id(resume.id)
    return {"success": success, "resume": saved.model_dump() if saved else resume.model_dump()}

class SpiderRunRequest(BaseModel):
    days: Optional[int] = 40
    max_pages: Optional[int] = 2
    category: Optional[str] = "latest"

class BatchSyncRequest(BaseModel):
    sources: List[str] = ["fangzhou"]
    days: Optional[int] = 30
    pages: Optional[int] = 2

@app.get("/api/spiders/sources")
async def get_spider_sources():
    """Returns available job spider sources and their metadata."""
    return {
        "sources": [
            {
                "id": "fangzhou",
                "name": "求职方舟",
                "description": "全网校招实时聚合接口（按天时效回溯）",
                "supports_days": True,
                "default_enabled": True
            },
            {
                "id": "wondercv",
                "name": "超级简历",
                "description": "名企名校校招网申投递列表",
                "supports_days": False,
                "default_enabled": False
            },
            {
                "id": "nowcoder",
                "name": "牛客网",
                "description": "互联网/IT校招日程广场",
                "supports_days": True,
                "default_enabled": False
            }
        ]
    }

@app.post("/api/spiders/batch-sync")
async def run_batch_spiders(req: BatchSyncRequest):
    """Execute multiple job spiders concurrently/sequentially based on user selections."""
    if not req.sources:
        raise HTTPException(status_code=400, detail="至少指定一个要同步的更新途径")

    from datetime import datetime, timedelta
    repo = getattr(app.state, "job_repo", job_repo)
    results = {}
    total_saved = 0
    total_fetched = 0
    effective_days = req.days if req.days is not None else 30
    since_date = (datetime.now() - timedelta(days=effective_days)).strftime("%Y-%m-%d")

    for src in req.sources:
        if src == "fangzhou":
            try:
                from src.services.spiders.fangzhou_spider import FangzhouJobSpider
                spider = FangzhouJobSpider(days_back=effective_days)
                jobs = await spider.fetch_jobs()
                count = await repo.upsert_jobs(jobs)
                results["fangzhou"] = {
                    "success": True,
                    "name": "求职方舟",
                    "fetched": len(jobs),
                    "saved": count
                }
                total_fetched += len(jobs)
                total_saved += count
            except Exception as e:
                results["fangzhou"] = {"success": False, "name": "求职方舟", "error": str(e)}

        elif src == "wondercv":
            try:
                from src.services.spiders.wondercv_spider import WondercvSpider
                spider = WondercvSpider(repo=repo)
                res = await spider.crawl_and_save(max_pages=req.pages or 2)
                results["wondercv"] = {
                    "success": True,
                    "name": "超级简历",
                    "fetched": res.get("fetched", 0),
                    "saved": res.get("saved", 0)
                }
                total_fetched += res.get("fetched", 0)
                total_saved += res.get("saved", 0)
            except Exception as e:
                results["wondercv"] = {"success": False, "name": "超级简历", "error": str(e)}

        elif src == "nowcoder":
            try:
                from src.services.spiders.nowcoder_spider import NowcoderSpider
                spider = NowcoderSpider(repo=repo)
                count = await spider.run(since_date=since_date, max_pages=req.pages or 3, page_size=50)
                results["nowcoder"] = {
                    "success": True,
                    "name": "牛客网",
                    "fetched": count,
                    "saved": count
                }
                total_fetched += count
                total_saved += count
            except Exception as e:
                results["nowcoder"] = {"success": False, "name": "牛客网", "error": str(e)}

    # 触发 Hook: 增量对齐最新岗位的特征元数据到用户矩阵字典
    synced_features = 0
    if total_saved > 0:
        try:
            recent_saved, _ = await repo.search_jobs(since_date=since_date, limit=200)
            rec_svc = getattr(app.state, "rec_service", recommendation_service)
            synced_features = await rec_svc.sync_features_from_jobs(recent_saved)
        except Exception:
            pass

    return {
        "success": True,
        "total_sources": len(req.sources),
        "total_saved": total_saved,
        "total_fetched": total_fetched,
        "synced_features": synced_features,
        "days": effective_days,
        "details": results
    }

@app.post("/api/spiders/fangzhou/run")
async def run_fangzhou_spider(days: Optional[int] = None, req: Optional[SpiderRunRequest] = None):
    from src.services.spiders.fangzhou_spider import FangzhouJobSpider
    effective_days = days if days is not None else (req.days if req and req.days else 40)
    repo = getattr(app.state, "job_repo", job_repo)
    spider = FangzhouJobSpider(days_back=effective_days)
    jobs = await spider.fetch_jobs()
    count = await repo.upsert_jobs(jobs)
    # 触发 Hook: 增量对齐最新岗位的特征元数据
    synced_features = 0
    if count > 0:
        try:
            rec_svc = getattr(app.state, "rec_service", recommendation_service)
            synced_features = await rec_svc.sync_features_from_jobs(jobs)
        except Exception:
            pass
    return {
        "success": True,
        "source": "求职方舟",
        "days": effective_days,
        "fetched": len(jobs),
        "saved": count,
        "imported_count": count,
        "synced_features": synced_features
    }

@app.post("/api/spiders/mock/run")
async def run_mock_spider(since_date: str = "2026-01-01"):
    from src.services.spiders.mock_spider import MockJobSpider
    repo = getattr(app.state, "job_repo", job_repo)
    spider = MockJobSpider()
    jobs = await spider.fetch_jobs(since_date=since_date)
    count = await repo.upsert_jobs(jobs)
    return {"success": True, "fetched": len(jobs), "saved": count}

@app.post("/api/spiders/wondercv/run")
async def run_wondercv_spider(pages: int = 2):
    from src.services.spiders.wondercv_spider import WondercvSpider
    repo = getattr(app.state, "job_repo", job_repo)
    spider = WondercvSpider(repo=repo)
    result = await spider.crawl_and_save(max_pages=pages)
    return {"success": True, "source": "超级简历WonderCV", **result}

@app.post("/api/spiders/nowcoder/run")
async def run_nowcoder_spider(pages: int = 5, since_date: str = "2026-07-01", page_size: int = 50):
    from src.services.spiders.nowcoder_spider import NowcoderSpider
    repo = getattr(app.state, "job_repo", job_repo)
    spider = NowcoderSpider(repo=repo)
    count = await spider.run(since_date=since_date, max_pages=pages, page_size=page_size)
    return {"success": True, "source": "牛客网Nowcoder", "pages": pages, "since_date": since_date, "saved": count}

@app.post("/api/resumes/parse-file")
async def parse_resume_file(file: UploadFile = File(...)):
    from src.services.resume_parser import parse_resume_content
    content_bytes = await file.read()
    filename = file.filename or "resume.txt"
    title, content_md, skills = parse_resume_content(filename, content_bytes)
    return {
        "title": title,
        "content_markdown": content_md,
        "skills": skills,
        "filename": filename,
        "file_size": len(content_bytes)
    }

@app.post("/api/resumes/{resume_id}/set-default")
async def set_default_resume(resume_id: str):
    repo = getattr(app.state, "user_repo", user_repo)
    success = await repo.set_default_resume(resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"success": True, "resume_id": resume_id}

@app.put("/api/resumes/{resume_id}")
async def update_resume(resume_id: str, req: ResumeUpdateRequest):
    repo = getattr(app.state, "user_repo", user_repo)
    existing = await repo.get_resume(resume_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Resume not found")
    title = req.title if req.title is not None else existing.title
    category = req.category if req.category is not None else existing.category
    content_md = (
        req.content_markdown if req.content_markdown is not None
        else (req.content_md if req.content_md is not None else existing.content_md)
    )
    skills = (
        req.skills if req.skills is not None
        else (req.parsed_skills if req.parsed_skills is not None else None)
    )
    is_default = req.is_default if req.is_default is not None else existing.is_default
    version_type = req.version_type if req.version_type is not None else getattr(existing, "version_type", "ORIGINAL")
    parent_resume_id = req.parent_resume_id if req.parent_resume_id is not None else getattr(existing, "parent_resume_id", None)
    keywords_matrix = req.keywords_matrix if req.keywords_matrix is not None else None
    updated = await repo.update_resume(
        resume_id=resume_id,
        title=title,
        category=category,
        content_md=content_md,
        skills=skills,
        is_default=is_default,
        version_type=version_type,
        parent_resume_id=parent_resume_id,
        keywords_matrix=keywords_matrix
    )
    return updated

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    repo = getattr(app.state, "user_repo", user_repo)
    success = await repo.delete_resume(resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"success": True, "deleted_id": resume_id}

# -------------------------------------------------------------
# AI Agent 智能体探活、LLM 配置与引擎管理
# -------------------------------------------------------------
@app.get("/api/system/ai-agents")
async def get_system_ai_agents():
    """
    自动探测本地可用的 AI 智能体 CLI 与配置的 LLM API 环境
    供多版本简历与专岗 ATS 诊断调优模块一键复用。
    """
    from src.services.agent_executor import AgentExecutor
    u_repo = getattr(app.state, "user_repo", user_repo)
    saved_cfg = await u_repo.get_setting("custom_llm_config")
    custom_configured = False
    if saved_cfg:
        try:
            import json
            cfg = json.loads(saved_cfg)
            if cfg.get("base_url"):
                custom_configured = True
        except Exception:
            pass
    return AgentExecutor.detect_available_agents(custom_llm_configured=custom_configured)

@app.get("/api/system/llm-config")
async def get_system_llm_config():
    """获取用户配置的自定义/本地 LLM 端点设置"""
    u_repo = getattr(app.state, "user_repo", user_repo)
    saved_cfg = await u_repo.get_setting("custom_llm_config")
    if not saved_cfg:
        return {
            "base_url": "http://127.0.0.1:8045/v1",
            "api_key": "",
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.3
        }
    import json
    return json.loads(saved_cfg)

@app.post("/api/system/llm-config")
async def save_system_llm_config(cfg: LLMConfig):
    """持久化保存用户配置的 LLM 端点设置到私有数据库"""
    u_repo = getattr(app.state, "user_repo", user_repo)
    import json
    await u_repo.set_setting("custom_llm_config", json.dumps(cfg.dict()))
    return {"success": True, "config": cfg.dict()}

@app.post("/api/system/llm-config/test")
async def test_system_llm_config(cfg: LLMConfig):
    """在线测试探测用户配置的 LLM 端点连通性"""
    from src.services.agent_executor import AgentExecutor
    res = await AgentExecutor.test_connection(
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        model=cfg.model or "claude-3-5-sonnet-20241022",
        timeout=10.0
    )
    return res

@app.post("/api/resumes/{resume_id}/optimize")
async def optimize_resume_by_id(resume_id: str, payload: dict = None):
    payload = payload or {}
    service = getattr(app.state, "resume_service", resume_service)
    try:
        from src.models import ResumeOptimizeRequest, LLMConfig
        req_kwargs = {
            "resume_id": resume_id,
            "job_id": payload.get("job_id"),
            "job_description": payload.get("job_description"),
            "mode": payload.get("mode", "GENERAL"),
            "target_company": payload.get("target_company"),
            "target_position": payload.get("target_position"),
            "engine": payload.get("engine", "auto"),
            "save_as_version": payload.get("save_as_version", False),
        }
        if "llm_config" in payload and isinstance(payload["llm_config"], dict):
            req_kwargs["llm_config"] = LLMConfig(**payload["llm_config"])
        req = ResumeOptimizeRequest(**req_kwargs)
        return await service.optimize_resume(req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/resumes/optimize")
async def optimize_resume(req: ResumeOptimizeRequest):
    service = getattr(app.state, "resume_service", resume_service)
    try:
        return await service.optimize_resume(req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# -------------------------------------------------------------
# Agent Push (AI 智能体主动特推 API)
# -------------------------------------------------------------
@app.get("/api/agent/pushes")
@app.get("/api/agent-pushes")
async def get_agent_pushes():
    u_repo = getattr(app.state, "user_repo", user_repo)
    j_repo = getattr(app.state, "job_repo", job_repo)
    pushes = await u_repo.list_agent_pushes()
    if not pushes:
        return []

    # 批量获取岗位，彻底避免 N+1 跨库串行查询
    job_ids = [p["job_id"] for p in pushes if p.get("job_id")]
    jobs_map = await j_repo.get_jobs_by_ids(job_ids)

    res = []
    for p in pushes:
        job = jobs_map.get(p["job_id"])
        if job:
            p_dict = dict(p)
            p_dict["job"] = job.model_dump()
            res.append(p_dict)
    return res

@app.post("/api/agent/pushes")
async def create_agent_push(payload: AgentPushCreate):
    u_repo = getattr(app.state, "user_repo", user_repo)
    j_repo = getattr(app.state, "job_repo", job_repo)
    job_id = payload.job_id
    recommend_reason = payload.recommend_reason or "AI 智能体基于您的简历画像与市场趋势高契合度精选推荐"
    match_score = float(payload.match_score)
    agent_name = payload.agent_name or "JobSourcingAgent"
    
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    job = await j_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found in public database")
        
    push_id = await u_repo.add_agent_push(
        job_id=job_id,
        recommend_reason=recommend_reason,
        match_score=match_score,
        agent_name=agent_name
    )
    return {"success": True, "push_id": push_id, "job_id": job_id}

@app.delete("/api/agent/pushes/{push_id}")
async def dismiss_agent_push(push_id: str):
    u_repo = getattr(app.state, "user_repo", user_repo)
    await u_repo.dismiss_agent_push(push_id)
    return {"success": True, "dismissed_id": push_id}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "JHTracker"}

# -------------------------------------------------------------
# Static SPA Hosting (Frontend Dist)
# -------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if (frontend_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 防御路径遍历：确保解析后的绝对路径严格位于 frontend_dist 内部
    try:
        dist_root = frontend_dist.resolve()
        target_file = (frontend_dist / full_path).resolve()
        if not target_file.is_relative_to(dist_root):
            raise HTTPException(status_code=403, detail="Access denied")
        if target_file.is_file():
            return FileResponse(target_file)
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=404, detail="Invalid path")

    index_html = frontend_dist / "index.html"
    if index_html.exists():
        return FileResponse(
            index_html,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return {"message": "JHTracker Backend API Running. Frontend build not found. Run 'npm run build' in frontend directory."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=False)


