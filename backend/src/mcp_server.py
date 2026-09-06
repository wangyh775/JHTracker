from typing import Optional, List, Dict, Any
try:
    from fastmcp import FastMCP
except (ImportError, Exception):
    try:
        from mcp.server.mcpserver import MCPServer as FastMCP
    except Exception:
        class FastMCP:
            def __init__(self, name="JHTracker-Engine"):
                self.name = name
            def tool(self):
                def decorator(fn):
                    return fn
                return decorator
            def run(self):
                pass
import hashlib
from datetime import datetime
from src.config import settings
from src.models import ApplicationItem, JobItem
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.recommendation_service import RecommendationService
from src.services.resume_service import ResumeService
from src.services.spiders.qiuzhifangzhou_spider import QiuzhifangzhouSpider
from src.security import sanitize_identifier, sanitize_text_input, validate_url
from src.logger import audit_mcp_tool

mcp = FastMCP("JHTracker-Engine")

job_repo = JobRepository(settings.public_db_path)
user_repo = UserRepository(settings.user_db_path)
rec_service = RecommendationService(job_repo, user_repo)
resume_service = ResumeService(job_repo, user_repo)

@mcp.tool()
@audit_mcp_tool(tool_name="job_search")
async def job_search(
    keyword: Optional[str] = None,
    keywords: Optional[str] = None,
    city: Optional[str] = None,
    company: Optional[str] = None,
    industry: Optional[str] = None,
    since_date: Optional[str] = None,
    days_limit: Optional[int] = None,
    time_filter: Optional[Dict[str, Any]] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """在公共岗位库中根据关键词、城市、行业及指定时间节点进行检索"""
    kw = keyword or keywords
    sd = since_date
    if not sd and days_limit:
        from datetime import datetime, timedelta
        sd = (datetime.now() - timedelta(days=days_limit)).strftime("%Y-%m-%d")
    elif not sd and time_filter:
        if time_filter.get("mode") == "since_date":
            sd = time_filter.get("since_date")
        elif time_filter.get("mode") == "relative" and time_filter.get("relative_months"):
            from datetime import datetime, timedelta
            sd = (datetime.now() - timedelta(days=time_filter["relative_months"] * 30)).strftime("%Y-%m-%d")
        elif time_filter.get("mode") == "range":
            sd = time_filter.get("start_date")

    jobs_res = await job_repo.search_jobs(
        keyword=kw,
        city=city,
        company=company,
        industry=industry,
        since_date=sd,
        limit=limit
    )
    if isinstance(jobs_res, tuple):
        jobs, _ = jobs_res
    else:
        jobs = jobs_res
    return [j.model_dump() for j in jobs]

@mcp.tool()
@audit_mcp_tool(tool_name="job_recommend")
async def job_recommend(
    resume_id: Optional[str] = None,
    min_score: float = 0.5,
    limit: int = 10,
    top_k: Optional[int] = None,
    since_date: Optional[str] = None,
    days_limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    基于系统内置规则和人在环路特征权重的候选粗筛/基线推荐接口。
    
    【重要提示对于智能体】：
    此接口仅提供底层规则与特征过滤（如硬门槛、城市、批次、IDF技能词命中）。
    若要向用户进行具有深度说服力的高价值【智能体特推 (job_agent_push)】，严禁直接照搬此接口结果！
    必须先调用 resume_get_profile 了解用户的学术课题、研究经历与硬技能，再针对性检索并进行语义对齐评估。
    """
    sd = since_date
    if not sd and days_limit:
        from datetime import datetime, timedelta
        sd = (datetime.now() - timedelta(days=days_limit)).strftime("%Y-%m-%d")
    return await rec_service.get_recommendations(
        resume_id=resume_id,
        min_score=min_score,
        limit=top_k or limit,
        since_date=sd
    )

@mcp.tool()
@audit_mcp_tool(tool_name="job_feedback")
async def job_feedback(
    job_id: str,
    action: str,
    reject_reasons: Optional[List[str]] = None
) -> Dict[str, Any]:
    """对推荐岗位进行人在环路反馈 (ACCEPT 进入待投递池，REJECT 触发特征降权抑制)"""
    return await rec_service.record_feedback(job_id, action, reject_reasons)

@mcp.tool()
@audit_mcp_tool(tool_name="job_agent_push")
async def job_agent_push(
    job_id: str,
    recommend_reason: str,
    match_score: float = 0.95,
    agent_name: str = "JobSourcingAgent"
) -> Dict[str, Any]:
    """
    AI 智能体主动向用户前端界面特推高价值岗位卡片。
    智能体基于对用户简历画像、市场趋势及全量岗位库的综合分析，提炼核心理由并直推到用户前端专属卡片区。
    
    【SOP 铁律要求】：
    1. 推送前必须已调用 resume_get_profile 获取用户的专业学术与课题背景；
    2. recommend_reason 严禁空泛敷衍，必须具体指出该岗位如何契合用户的课题、专业技能或求职偏好（建议不少于 12 个字）；
    3. 严格遵守企业去重与频控铁律（已投递企业不推，待投递满 3 岗企业不推）。
    
    参数:
    - job_id: 岗位唯一 ID
    - recommend_reason: 智能体推荐的具体理由 (必须指出对口课题或技能)
    - match_score: 匹配度契合打分 (0.0 ~ 1.0, 默认 0.95)
    - agent_name: 智能体标识名称
    """
    if not recommend_reason or len(recommend_reason.strip()) < 8:
        return {
            "success": False,
            "error": "推荐理由过短或空泛。推送理由必须具体指明该岗位对标用户的哪个专业方向、课题或核心技能点。"
        }
    job = await job_repo.get_job_by_id(job_id)
    if not job:
        return {"success": False, "error": f"Job ID '{job_id}' not found in public database"}

    # 企业级去重与频控校验：已投递企业拦截、待投递列表限额拦截 (<=3)
    app_status = await user_repo.get_company_application_status()
    applied_companies = app_status["applied_companies"]
    capped_pending_companies = app_status["capped_pending_companies"]
    pending_counts = app_status["pending_counts"]

    company_name = (job.company or "").strip()
    if company_name in applied_companies:
        return {
            "success": False,
            "error": f"企业【{company_name}】已被用户投递，根据防打扰规则不再进行推送。",
            "job_id": job_id,
            "company": company_name
        }

    if company_name in capped_pending_companies or pending_counts.get(company_name, 0) >= 3:
        return {
            "success": False,
            "error": f"企业【{company_name}】在待投递列表中已有 {pending_counts.get(company_name, 0)} 个岗位（已达上限 3 个），暂停推送该企业新岗位。",
            "job_id": job_id,
            "company": company_name
        }
    
    push_id = await user_repo.add_agent_push(
        job_id=job_id,
        recommend_reason=recommend_reason,
        match_score=match_score,
        agent_name=agent_name
    )
    return {
        "success": True,
        "push_id": push_id,
        "job_id": job_id,
        "title": job.title,
        "company": job.company,
        "message": "Successfully pushed to user's AI Agent recommendation cards zone."
    }

@mcp.tool()
@audit_mcp_tool(tool_name="resume_get_profile")
async def resume_get_profile(
    resume_id: Optional[str] = None
) -> Dict[str, Any]:
    """获取简历画像信息 (技能标签、目标方向与内容摘要)，用于岗位匹配分析。智能体对用户原始简历仅有只读权限。"""
    if resume_id:
        clean_id = sanitize_identifier(resume_id)
        if not clean_id:
            return {"found": False, "error": f"Invalid resume_id: '{resume_id}'"}
        resume = await user_repo.get_resume(clean_id)
    else:
        resume = await user_repo.get_default_resume()

    if not resume:
        return {"found": False, "error": "No resume found"}

    return {
        "found": True,
        "resume_id": resume.id,
        "title": resume.title,
        "category": resume.category,
        "version_type": getattr(resume, "version_type", "ORIGINAL"),
        "parent_resume_id": getattr(resume, "parent_resume_id", None),
        "skills": resume.parsed_skills or [],
        "content_preview": (resume.content_md[:500] + "...") if resume.content_md and len(resume.content_md) > 500 else (resume.content_md or ""),
        "is_default": bool(resume.is_default),
        "is_read_only_original": getattr(resume, "version_type", "ORIGINAL") == "ORIGINAL"
    }

@mcp.tool()
@audit_mcp_tool(tool_name="resume_optimize")
async def resume_optimize(
    resume_id: str,
    job_id: Optional[str] = None,
    optimization_type: str = "GENERAL",
    save_as_ai_version: bool = True
) -> Dict[str, Any]:
    """
    针对目标岗位或通用要求对简历进行 ATS 匹配度分析与优化。
    安全规则：用户的原始简历严格只读，智能体绝不能覆写原始简历；AI 优化结果将保存为独立的 AI_OPTIMIZED 版本或仅返回润色建议。
    """
    clean_resume_id = sanitize_identifier(resume_id)
    if not clean_resume_id:
        return {"success": False, "error": f"Invalid resume_id format: '{resume_id}'"}

    clean_job_id = sanitize_identifier(job_id) if job_id else None

    try:
        res = await resume_service.optimize_resume(
            resume_id=clean_resume_id,
            job_id=clean_job_id,
            optimization_type=optimization_type,
            save_as_version=save_as_ai_version
        )
        return {
            "success": True,
            **res
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
@audit_mcp_tool(tool_name="job_sync_run")
async def job_sync_run(
    source: str = "qiuzhifangzhou",
    category: str = "latest",
    limit: int = 50,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """触发定向爬虫同步，抓取最新校招/实习/社招岗位数据并去重入库"""
    clean_src = sanitize_text_input(source, max_len=30).lower()
    clean_cat = sanitize_text_input(category, max_len=30)
    limit = max(1, min(limit, 200))

    saved_total = 0
    if clean_src in ("qiuzhifangzhou", "fangzhou"):
        spider = QiuzhifangzhouSpider(job_repo)
        result = await spider.crawl_and_save(table=clean_cat, max_pages=max(1, limit // 15))
        saved_total = result.get("saved", 0)
        res_data = {
            "success": True,
            "source": clean_src,
            "category": clean_cat,
            "fetched": result.get("fetched", 0),
            "saved": saved_total
        }
    elif clean_src in ("wondercv", "chaojijianli"):
        from src.services.spiders.wondercv_spider import WondercvSpider
        spider = WondercvSpider(job_repo)
        result = await spider.crawl_and_save(max_pages=max(1, limit // 20))
        saved_total = result.get("saved", 0)
        res_data = {
            "success": True,
            "source": clean_src,
            "category": clean_cat,
            "fetched": result.get("fetched", 0),
            "saved": saved_total
        }
    elif clean_src in ("nowcoder", "niuke"):
        from src.services.spiders.nowcoder_spider import NowcoderSpider
        spider = NowcoderSpider(job_repo)
        pages = max(1, limit // 50)
        saved = await spider.run(max_pages=pages, page_size=50)
        saved_total = saved
        res_data = {
            "success": True,
            "source": clean_src,
            "category": clean_cat,
            "pages": pages,
            "saved": saved_total
        }
    else:
        return {
            "success": False,
            "error": f"Unsupported crawler source: '{source}'. Currently supported: 'qiuzhifangzhou', 'wondercv', 'nowcoder'"
        }

    # 触发 Hook: 增量对齐最新抓取岗位的特征元数据
    if saved_total > 0:
        try:
            recent_jobs, _ = await job_repo.search_jobs(limit=saved_total)
            synced = await rec_service.sync_features_from_jobs(recent_jobs)
            res_data["synced_features"] = synced
        except Exception:
            pass

    return res_data

@mcp.tool()
@audit_mcp_tool(tool_name="job_get_detail")
async def job_get_detail(
    job_id: str
) -> Dict[str, Any]:
    """获取指定岗位的完整公开信息，包括原始公告、投递原链接及内推码等"""
    clean_id = sanitize_identifier(job_id)
    if not clean_id:
        return {"found": False, "error": f"Invalid job_id format: '{job_id}'"}

    job = await job_repo.get_job_by_id(clean_id)
    if not job:
        return {"found": False, "error": f"Job with id '{clean_id}' not found"}

    return {
        "found": True,
        **job.model_dump()
    }

@mcp.tool()
@audit_mcp_tool(tool_name="job_add_external")
async def job_add_external(
    title: str,
    company: str,
    location: Optional[str] = "全国",
    salary_range: Optional[str] = "面议",
    detail_url: Optional[str] = None,
    description: Optional[str] = None,
    industry: Optional[str] = "综合",
    source_site: Optional[str] = "agent_discovered",
    referral_code: Optional[str] = None,
    type_tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """智能体将外部渠道（如小红书、牛客、Boss直聘、企业官网、公众号等）检索到的招聘信息去重录入全量公共库"""
    clean_title = sanitize_text_input(title, max_len=200)
    clean_company = sanitize_text_input(company, max_len=200)
    clean_location = sanitize_text_input(location or "全国", max_len=100)

    if not clean_title or not clean_company:
        return {
            "success": False,
            "error": "岗位名称 (title) 和 公司名称 (company) 为必填项且不能为空"
        }

    clean_url = validate_url(detail_url) if detail_url else None
    if detail_url and not clean_url:
        return {
            "success": False,
            "error": "提供的 detail_url 格式不合法，必须为标准 http/https 链接"
        }

    clean_salary = sanitize_text_input(salary_range or "面议", max_len=50)
    clean_desc = sanitize_text_input(description or "", max_len=10000)
    clean_ind = sanitize_text_input(industry or "综合", max_len=100)
    clean_src = sanitize_text_input(source_site or "agent_discovered", max_len=50)
    clean_ref = sanitize_text_input(referral_code or "", max_len=50) if referral_code else None

    # 基于 公司名 + 岗位名 + 工作地点 生成确定性哈希，确保幂等与防重更新（加长至 16 位降低碰撞）
    unique_str = f"{clean_company.strip()}_{clean_title.strip()}_{clean_location.strip()}"
    job_hash = hashlib.md5(unique_str.encode("utf-8")).hexdigest()[:16]
    job_id = f"ext_{job_hash}"

    tags = ["外部录入"]
    if type_tags and isinstance(type_tags, list):
        for t in type_tags:
            sanitized_t = sanitize_text_input(str(t), max_len=30)
            if sanitized_t and sanitized_t not in tags:
                tags.append(sanitized_t)

    job_item = JobItem(
        id=job_id,
        title=clean_title,
        company=clean_company,
        location=clean_location,
        industry=clean_ind,
        salary_range=clean_salary,
        publish_date=datetime.now().strftime("%Y-%m-%d"),
        detail_url=clean_url,
        description=clean_desc,
        source_site=clean_src,
        type_tags=tags,
        referral_code=clean_ref
    )

    saved_count = await job_repo.upsert_jobs([job_item])

    # 触发 Hook: 增量对齐该外部岗位的特征元数据到用户矩阵字典
    synced_features = 0
    if saved_count > 0:
        try:
            synced_features = await rec_service.sync_features_from_jobs([job_item])
        except Exception:
            pass

    return {
        "success": True,
        "job_id": job_id,
        "action": "upserted",
        "saved_count": saved_count,
        "synced_features": synced_features,
        "message": f"成功将岗位 [{clean_company} - {clean_title}] 幂等录入全量库"
    }

def main():
    mcp.run()

if __name__ == "__main__":
    main()
