import os
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_, and_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from backend.app.core.database import get_db
from backend.app.models.entities import (
    Company, Job, Application, ApplicationSubmission, InterviewFeedback, Memory, Note, AgentTrace, Resume
)
from backend.app.models.schemas import (
    CompanyOut, CompanyCreate, CompanyUpdate,
    JobOut, JobCreate,
    ApplicationOut, ApplicationCreate, ApplicationUpdate, ApplicationListResponse,
    ToApplyJobOut,
    SubmissionOut, SubmissionCreate, SubmissionUpdate,
    InterviewFeedbackOut, InterviewFeedbackCreate,
    MemoryOut, MemoryCreate,
    AutofillRequest, AutofillResponse,
    TrackMatchRequest, TrackMatchResult
)
from backend.app.services.autofill.manager import CDPManager
from backend.app.services.router import ResumeRouter

router = APIRouter(prefix="/api/v1")
cdp_manager = CDPManager()

# --- 1. Health Check ---
@router.get("/health")
async def health_check():
    cdp_ok = cdp_manager.is_cdp_available()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "cdp_available": cdp_ok,
        "mode": "async-fastapi"
    }

# --- 2. Dashboard Briefing & Analytics ---
@router.get("/dashboard/briefing")
async def get_dashboard_briefing(db: AsyncSession = Depends(get_db)):
    comp_res = await db.execute(select(Company))
    total_companies = len(comp_res.scalars().all())

    app_res = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
    )
    all_apps = app_res.scalars().all()

    applied_count = sum(1 for a in all_apps if a.status not in ["待审核", "待投递", "待提交", "已放弃"])
    interview_count = sum(1 for a in all_apps if "面" in (a.status or "") or "笔试" in (a.status or ""))
    offer_count = sum(1 for a in all_apps if "offer" in (a.status or "").lower() or "录用" in (a.status or ""))
    pending_approval = sum(1 for a in all_apps if a.status in ["待审核", "Pending Approval"])
    to_apply_count = sum(1 for a in all_apps if a.status == "待投递" and not a.is_archived)

    # 超过7天无响应预警
    stale_unanswered = []
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    for a in all_apps:
        if not a.is_archived and a.status in ["已投递", "简历筛选"] and a.apply_date and a.apply_date < seven_days_ago:
            stale_unanswered.append({
                "id": a.id,
                "company_name": a.company.name if a.company else "未知企业",
                "position": a.position,
                "status": a.status,
                "apply_date": a.apply_date.strftime("%Y-%m-%d") if a.apply_date else "",
                "days_elapsed": (now - a.apply_date).days
            })

    # 高匹配待投递/待审核
    high_match_pending = []
    for a in all_apps:
        if not a.is_archived and a.status in ["待审核", "Pending Approval", "待投递"] and (a.match_score or 0) >= 75:
            high_match_pending.append({
                "id": a.id,
                "company_name": a.company.name if a.company else "未知企业",
                "position": a.position,
                "match_score": a.match_score,
                "scoring_reason": a.scoring_reason or a.agent_reason
            })

    active_applications_count = sum(1 for a in all_apps if not a.is_archived)
    archived_applications_count = sum(1 for a in all_apps if a.is_archived)

    # 4轨分布统计
    track_distribution = {
        "control": sum(1 for a in all_apps if a.track == "control"),
        "embedded_auto": sum(1 for a in all_apps if a.track == "embedded_auto"),
        "mechatronics": sum(1 for a in all_apps if a.track == "mechatronics"),
        "mechanical_cfd": sum(1 for a in all_apps if a.track == "mechanical_cfd"),
        "other": sum(1 for a in all_apps if a.track not in ["control", "embedded_auto", "mechatronics", "mechanical_cfd"])
    }

    return {
        "active_applications_count": active_applications_count,
        "archived_applications_count": archived_applications_count,
        "track_distribution": track_distribution,
        "stats": {
            "total_companies": total_companies,
            "applied_count": applied_count,
            "interview_count": interview_count,
            "offer_count": offer_count,
            "pending_approval": pending_approval,
            "to_apply_count": to_apply_count,
            "active_count": active_applications_count,
            "archived_count": archived_applications_count
        },
        "stale_unanswered": stale_unanswered[:5],
        "high_match_pending": high_match_pending[:5]
    }

# --- 3. Companies ---
@router.get("/companies", response_model=List[CompanyOut])
async def list_companies(tier: Optional[str] = None, city: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Company).order_by(Company.created_at.desc())
    if tier:
        query = query.where(Company.tier == tier)
    if city:
        query = query.where(Company.city.contains(city))
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/companies", response_model=CompanyOut)
async def create_company(payload: CompanyCreate, db: AsyncSession = Depends(get_db)):
    company = Company(**payload.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

# --- 4. Jobs ---
@router.get("/jobs", response_model=List[JobOut])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).options(selectinload(Job.company)).order_by(Job.created_at.desc()))
    return result.scalars().all()

# --- 5. Applications (Workbench Table & Kanban) ---
@router.get("/applications", response_model=ApplicationListResponse)
async def list_applications(
    is_archived: Optional[bool] = Query(None, description="是否获取归档记录"),
    active: Optional[bool] = Query(None, description="是否获取活跃记录(与is_archived互逆)"),
    status: Optional[str] = Query(None, description="状态筛选"),
    track: Optional[str] = Query(None, description="4轨筛选"),
    search: Optional[str] = Query(None, description="搜索公司名或岗位名"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    base_query = select(Application).options(
        selectinload(Application.company),
        selectinload(Application.job),
        selectinload(Application.resume)
    )

    # 统计活跃与归档总数
    active_cnt_res = await db.execute(select(func.count(Application.id)).where(Application.is_archived == False))
    active_count = active_cnt_res.scalar() or 0

    archived_cnt_res = await db.execute(select(func.count(Application.id)).where(Application.is_archived == True))
    archived_count = archived_cnt_res.scalar() or 0

    # 确定是否归档
    target_archived = False
    if is_archived is not None:
        target_archived = is_archived
    elif active is not None:
        target_archived = not active

    # 过滤条件
    conditions = [Application.is_archived == target_archived]
    if status:
        conditions.append(Application.status == status)
    if track:
        conditions.append(Application.track == track)
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Application.position.ilike(search_pattern),
                Application.company.has(Company.name.ilike(search_pattern))
            )
        )

    filtered_query = base_query.where(and_(*conditions))
    total_res = await db.execute(select(func.count(Application.id)).where(and_(*conditions)))
    total = total_res.scalar() or 0

    # 排序与分页
    paged_query = filtered_query.order_by(Application.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items_res = await db.execute(paged_query)
    items = items_res.scalars().all()

    return ApplicationListResponse(
        items=items,
        total=total,
        active_count=active_count,
        archived_count=archived_count,
        page=page,
        page_size=page_size
    )

@router.get("/applications/{app_id}", response_model=ApplicationOut)
async def get_application(app_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Application)
        .options(
            selectinload(Application.company),
            selectinload(Application.job),
            selectinload(Application.resume),
            selectinload(Application.submissions),
            selectinload(Application.feedbacks)
        )
        .where(Application.id == app_id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.post("/applications", response_model=ApplicationOut)
async def create_application(payload: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()
    company_id = data.get("company_id")
    pos_val = (data.get("position") or "待定岗位").strip()

    # Deduplication check for company_id + position across all application records (同一公司同一岗位全量去重)
    res_existing = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
        .where(
            Application.company_id == company_id,
            func.lower(func.trim(Application.position)) == pos_val.lower()
        )
    )
    existing_app = res_existing.scalar_one_or_none()
    if existing_app:
        return existing_app

    # 自动解析 4 轨与简历版本
    if data.get("track") in [None, "general"]:
        track_key, track_name, _, _, _, _ = ResumeRouter.resolve_track(data.get("position", ""), data.get("notes", ""))
        data["track"] = track_key
        data["resume_version"] = track_name

    app = Application(**data)
    db.add(app)
    await db.commit()
    await db.refresh(app)
    
    # 重新加载关联关系
    res = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
        .where(Application.id == app.id)
    )
    return res.scalar_one()

@router.put("/applications/{app_id}", response_model=ApplicationOut)
async def update_application(app_id: int, payload: ApplicationUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Application).where(Application.id == app_id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(app, field, value)

    # 状态变化自动处理
    if app.status == "已投递" and not app.apply_date:
        app.apply_date = datetime.utcnow()

    app.updated_at = datetime.utcnow()
    await db.commit()

    res = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
        .where(Application.id == app.id)
    )
    return res.scalar_one()

@router.post("/applications/{app_id}/archive", response_model=ApplicationOut)
async def archive_application(app_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Application).where(Application.id == app_id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.is_archived = True
    app.archived_at = datetime.utcnow()
    await db.commit()
    
    res = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
        .where(Application.id == app.id)
    )
    return res.scalar_one()

@router.post("/applications/{app_id}/unarchive", response_model=ApplicationOut)
async def unarchive_application(app_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Application).where(Application.id == app_id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app.is_archived = False
    app.archived_at = None
    await db.commit()
    
    res = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
        .where(Application.id == app.id)
    )
    return res.scalar_one()

@router.post("/applications/archive-stale")
async def archive_stale_applications(
    days_threshold: int = Body(15, embed=True),
    db: AsyncSession = Depends(get_db)
):
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    query = select(Application).where(
        Application.is_archived == False,
        Application.updated_at < cutoff,
        Application.status.in_(["已投递", "简历筛选", "待投递", "已放弃", "已拒"])
    )
    res = await db.execute(query)
    stale_apps = res.scalars().all()
    affected_ids = []
    for a in stale_apps:
        a.is_archived = True
        a.archived_at = datetime.utcnow()
        affected_ids.append(a.id)
    await db.commit()
    return {"archived_count": len(affected_ids), "affected_ids": affected_ids}

@router.delete("/applications/{app_id}")
async def delete_application(app_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Application).where(Application.id == app_id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
    await db.commit()
    return {"success": True, "id": app_id}

# --- 6. To-Apply Pool ---
@router.get("/to-apply", response_model=List[ToApplyJobOut])
async def list_to_apply_jobs(
    track: Optional[str] = None,
    min_score: float = 0.0,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Job).options(selectinload(Job.company)).where(Job.status == "open")
    if search:
        query = query.where(Job.title.ilike(f"%{search}%"))
    
    result = await db.execute(query)
    jobs = result.scalars().all()

    to_apply_list = []
    for j in jobs:
        # 解析 4 轨
        track_key, track_name, pdf_path, greeting, skills, conf = ResumeRouter.resolve_track(
            j.title, (j.job_description or "") + " " + (j.requirements or "")
        )
        if track and track_key != track:
            continue
        
        match_score = j.match_score if (j.match_score and j.match_score > 0) else round(conf * 100, 1)
        if match_score < min_score:
            continue

        pdf_filename = os.path.basename(pdf_path)
        to_apply_list.append(ToApplyJobOut(
            id=j.id,
            company_id=j.company_id,
            company_name=j.company.name if j.company else "未知企业",
            company_tier=j.company.tier if j.company else "B",
            company_city=j.company.city if j.company else "",
            title=j.title,
            department=j.department,
            location=j.location,
            salary_range=j.salary_range,
            job_url=j.job_url,
            job_description=j.job_description,
            match_score=match_score,
            track=track_key,
            track_name=track_name,
            recommended_resume=pdf_filename,
            greeting_copy=greeting,
            created_at=j.created_at
        ))

    to_apply_list.sort(key=lambda x: x.match_score, reverse=True)
    return to_apply_list

@router.post("/to-apply/{job_id}/prefill", response_model=AutofillResponse)
async def prefill_to_apply_job(job_id: int, payload: AutofillRequest, db: AsyncSession = Depends(get_db)):
    job_res = await db.execute(select(Job).options(selectinload(Job.company)).where(Job.id == job_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    track_key, track_name, resume_path, greeting, _, _ = ResumeRouter.resolve_track(job.title, job.job_description or "")
    if payload.resume_track and payload.resume_track in ResumeRouter.TRACKS:
        track_info = ResumeRouter.TRACKS[payload.resume_track]
        resume_path = os.path.join(ResumeRouter.RESUMES_DIR, track_info["pdf_name"])
        track_key = payload.resume_track
        track_name = track_info["name"]

    # 1. 查找或创建 Application
    app_res = await db.execute(select(Application).where(Application.job_id == job.id))
    app = app_res.scalar_one_or_none()
    if not app:
        app = Application(
            company_id=job.company_id,
            job_id=job.id,
            position=job.title,
            status="待提交",
            track=track_key,
            resume_version=track_name,
            source_url=job.job_url,
            match_score=job.match_score or 85.0
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)

    # 2. 执行 CDP 预填
    result = await cdp_manager.autofill_active_tab(resume_path=resume_path)
    
    # 3. 创建 Submission 快照
    submission = ApplicationSubmission(
        application_id=app.id,
        form_url=job.job_url or "active_browser_tab",
        prefilled_data=json.dumps(result.get("prefilled_fields", {}), ensure_ascii=False),
        status="pending_audit" if result.get("success") else "failed",
        failure_reason=result.get("message") if not result.get("success") else None,
        resume_used=os.path.basename(resume_path)
    )
    db.add(submission)
    app.status = "待提交"
    await db.commit()
    await db.refresh(submission)

    result["submission_id"] = submission.id
    return AutofillResponse(**result)

# --- 7. Zero-Submit Submissions ---
@router.get("/submissions", response_model=List[SubmissionOut])
async def list_submissions(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(ApplicationSubmission).options(
        selectinload(ApplicationSubmission.application).selectinload(Application.company)
    ).order_by(ApplicationSubmission.created_at.desc())
    if status:
        query = query.where(ApplicationSubmission.status == status)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/submissions/{sub_id}", response_model=SubmissionOut)
async def get_submission(sub_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ApplicationSubmission)
        .options(
            selectinload(ApplicationSubmission.application).selectinload(Application.company),
            selectinload(ApplicationSubmission.application).selectinload(Application.job)
        )
        .where(ApplicationSubmission.id == sub_id)
    )
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission snapshot not found")
    return sub

@router.put("/submissions/{sub_id}", response_model=SubmissionOut)
async def update_submission(sub_id: int, payload: SubmissionUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ApplicationSubmission).where(ApplicationSubmission.id == sub_id))
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission snapshot not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(sub, k, v)
    sub.updated_at = datetime.utcnow()
    await db.commit()

    res = await db.execute(
        select(ApplicationSubmission)
        .options(selectinload(ApplicationSubmission.application).selectinload(Application.company))
        .where(ApplicationSubmission.id == sub.id)
    )
    return res.scalar_one()

@router.post("/submissions/{sub_id}/confirm", response_model=ApplicationOut)
async def confirm_submission(sub_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ApplicationSubmission)
        .options(selectinload(ApplicationSubmission.application))
        .where(ApplicationSubmission.id == sub_id)
    )
    sub = res.scalar_one_or_none()
    if not sub or not sub.application:
        raise HTTPException(status_code=404, detail="Submission or associated application not found")
    
    sub.status = "submitted"
    sub.submitted_at = datetime.utcnow()
    sub.human_approved_at = datetime.utcnow()
    
    app = sub.application
    app.status = "已投递"
    app.apply_date = datetime.utcnow()
    app.updated_at = datetime.utcnow()
    
    await db.commit()

    res = await db.execute(
        select(Application)
        .options(selectinload(Application.company), selectinload(Application.job))
        .where(Application.id == app.id)
    )
    return res.scalar_one()

# --- 8. Feedbacks & Memories ---
@router.get("/feedbacks", response_model=List[InterviewFeedbackOut])
async def list_feedbacks(application_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(InterviewFeedback).order_by(InterviewFeedback.created_at.desc())
    if application_id:
        query = query.where(InterviewFeedback.application_id == application_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/feedbacks", response_model=InterviewFeedbackOut)
async def create_feedback(payload: InterviewFeedbackCreate, db: AsyncSession = Depends(get_db)):
    fb = InterviewFeedback(**payload.model_dump())
    db.add(fb)
    # 同步更新 Application 的 interview_date
    if fb.interview_date:
        app_res = await db.execute(select(Application).where(Application.id == fb.application_id))
        app = app_res.scalar_one_or_none()
        if app:
            app.interview_date = fb.interview_date
            if app.status in ["已投递", "简历筛选", "笔试"]:
                app.status = f"面试({fb.round})"
    await db.commit()
    await db.refresh(fb)
    return fb

@router.get("/memories", response_model=List[MemoryOut])
async def list_memories(category: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Memory).where(Memory.is_active == True).order_by(Memory.created_at.desc())
    if category:
        query = query.where(Memory.category == category)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/memories", response_model=MemoryOut)
async def create_memory(payload: MemoryCreate, db: AsyncSession = Depends(get_db)):
    mem = Memory(**payload.model_dump())
    db.add(mem)
    await db.commit()
    await db.refresh(mem)
    return mem

# --- 9. Router Recommendation & Match ---
@router.post("/router/match", response_model=TrackMatchResult)
async def match_track(payload: TrackMatchRequest):
    track_key, track_name, pdf_path, greeting, skills, conf = ResumeRouter.resolve_track(
        payload.job_title, payload.job_description or ""
    )
    track_info = ResumeRouter.TRACKS.get(track_key, {})
    return TrackMatchResult(
        track_key=track_key,
        track_name=track_name,
        pdf_name=track_info.get("pdf_name", "王云鹤_简历_综合.pdf"),
        pdf_path=pdf_path,
        greeting_template=track_info.get("greeting_template", ""),
        greeting_copy=greeting,
        highlight_skills=skills,
        confidence_score=conf
    )

@router.get("/router/recommend")
async def recommend_resume_and_script(position: str, description: str = ""):
    track_key, track_name, pdf_path, greeting, skills, conf = ResumeRouter.resolve_track(position, description)
    return {
        "track_key": track_key,
        "recommended_track": track_name,
        "resume_pdf": pdf_path,
        "greeting_script": greeting,
        "highlight_skills": skills,
        "confidence_score": conf
    }

# --- 10. Agent Traces ---
@router.get("/traces")
async def list_agent_traces(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentTrace).order_by(AgentTrace.created_at.desc()).limit(limit))
    traces = result.scalars().all()
    return [
        {
            "id": t.id,
            "agent_name": t.agent_name,
            "action": t.action,
            "target_type": t.target_type,
            "target_id": t.target_id,
            "details": t.details,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else ""
        }
        for t in traces
    ]

# --- 11. Answer Bank ---
@router.get("/answer-bank")
async def get_answer_bank():
    return [
        {
            "id": 1,
            "category": "控制算法 (MPC/EKF)",
            "question": "为什么温控要用 MPC 模型预测控制而不是传统 PID？",
            "answer": "FDM 挤出热端存在显著的大纯滞后（热容传递延迟）与非线性相变热扰动。在400℃以上挤出速度突变时，传统PID超调量大且极易产生稳态震荡。我们建立热端三节点非线性状态空间方程，利用MPC滚动优化提前预判热量损耗，配合EKF在线滤除热电偶高频噪声，实现稳态控温误差 < 0.5℃，动态恢复时间缩短60%。",
            "keywords": ["MPC", "状态空间", "EKF", "温控闭环"]
        },
        {
            "id": 2,
            "category": "流热耦合与仿真 (CFD)",
            "question": "面向 PEEK 的喷头流热固耦合仿真中湍流模型与流变模型如何选取？",
            "answer": "腔体内热风循环选用 k-ω SST 湍流模型，能精确捕捉近壁面高剪切流动与远场自由流；喷头熔融管内 PEEK 属于典型非牛顿剪切变稀流体，引入 Cross-WLF 黏度模型并考虑温度依赖性，相变区采用焓-多孔介质法模拟固液相变，搭建高温推力测试台实测推力与仿真误差 < 2%。",
            "keywords": ["Fluent", "k-w SST", "Cross-WLF", "PEEK"]
        },
        {
            "id": 3,
            "category": "机械结构与整机设计",
            "question": "500mm 大行程 Z 轴四丝杠同步升降如何防止机械过约束与卡死？",
            "answer": "500mm全金属机架采用四组滚珠丝杠配合直线导轨。为避免多点过约束卡滞，采用‘单电机+闭环同步带轮传动’驱动四轴同步旋转，在丝母与热床托架连接处设计柔性浮动连接结构释放热膨胀应力与微小安装平行度误差，热床平面度调优至 0.08mm 以内。",
            "keywords": ["CoreXY", "四丝杠同步", "浮动连接", "SolidWorks"]
        },
        {
            "id": 4,
            "category": "工业电气与抗震控制柜",
            "question": "高铁地震预警控制柜在抗震与工业防干扰上采取了哪些规范？",
            "answer": "严格执行工控防干扰规范进行强弱电物理分层隔离与线槽走线，柜内关键主控与采集模块安装阻尼减震垫圈。针对高速信号线采用双端接地屏蔽层，电源输入端配置工业级 EMC 滤波器，在模拟振动台（10Hz-150Hz）扫频测试下信号无突变跳动。",
            "keywords": ["EPLAN", "EMC滤波", "抗震机柜", "屏蔽走线"]
        }
    ]

# --- 12. Offer Compare Calculator ---
@router.post("/compare/calculate")
async def calculate_offer_comparison(payload: Dict[str, Any]):
    base_salary = float(payload.get("monthly_base", 20000))
    months = float(payload.get("months", 15))
    fund_rate = float(payload.get("housing_fund_rate", 0.12))
    city = payload.get("city", "苏州")

    annual_gross = base_salary * months
    monthly_fund = base_salary * fund_rate * 2
    annual_fund = monthly_fund * 12

    taxable = max(0.0, annual_gross - 60000 - (base_salary * 0.22 * 12))
    tax = taxable * 0.1
    net_take_home = annual_gross - tax - (base_salary * 0.10 * 12)

    return {
        "annual_gross": annual_gross,
        "annual_net": round(net_take_home, 2),
        "annual_housing_fund": round(annual_fund, 2),
        "monthly_housing_fund": round(monthly_fund, 2),
        "total_benefit_package": round(net_take_home + annual_fund, 2),
        "city_rating": f"{city} (公积金全额缴纳对30岁置业极其有利)"
    }
