from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    name_alias: Optional[str] = None
    tier: Optional[str] = 'B'
    priority: Optional[str] = 'B'
    scale: Optional[str] = None
    financing_stage: Optional[str] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    sub_city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    careers_url: Optional[str] = None
    source_list: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    tags: Optional[str] = None
    score: Optional[int] = 0
    score_reason: Optional[str] = None
    notes: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    name_alias: Optional[str] = None
    tier: Optional[str] = None
    priority: Optional[str] = None
    scale: Optional[str] = None
    financing_stage: Optional[str] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    sub_city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    careers_url: Optional[str] = None
    source_list: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    tags: Optional[str] = None
    score: Optional[int] = None
    score_reason: Optional[str] = None
    notes: Optional[str] = None

class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JobBase(BaseModel):
    company_id: int
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = 'open'
    track: Optional[str] = None
    match_score: Optional[float] = 0.0

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    company: Optional[CompanyOut] = None


class ResumeBase(BaseModel):
    name: str
    version: Optional[str] = None
    file_path: str
    file_type: Optional[str] = 'pdf'
    file_size: Optional[int] = None
    track: Optional[str] = None
    note: Optional[str] = None
    is_default: Optional[bool] = False

class ResumeOut(ResumeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


class ApplicationBase(BaseModel):
    company_id: int
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    position: str
    status: Optional[str] = '待投递'
    channel: Optional[str] = None
    track: Optional[str] = 'general'
    apply_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    resume_version: Optional[str] = '通用版'
    form_type: Optional[str] = 'structured'
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    match_score: Optional[float] = 0.0
    scoring_reason: Optional[str] = None
    agent_reason: Optional[str] = None
    agent_task_id: Optional[str] = None
    feedback: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    offer_salary: Optional[str] = None
    offer_status: Optional[str] = None
    is_archived: Optional[bool] = False
    archived_at: Optional[datetime] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    company_id: Optional[int] = None
    job_id: Optional[int] = None
    resume_id: Optional[int] = None
    position: Optional[str] = None
    status: Optional[str] = None
    channel: Optional[str] = None
    track: Optional[str] = None
    apply_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    resume_version: Optional[str] = None
    form_type: Optional[str] = None
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    match_score: Optional[float] = None
    scoring_reason: Optional[str] = None
    feedback: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    offer_salary: Optional[str] = None
    offer_status: Optional[str] = None
    is_archived: Optional[bool] = None
    archived_at: Optional[datetime] = None

class ApplicationOut(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    company: Optional[CompanyOut] = None
    job: Optional[JobOut] = None
    resume: Optional[ResumeOut] = None


class ApplicationListResponse(BaseModel):
    items: List[ApplicationOut]
    total: int
    active_count: int
    archived_count: int
    page: int
    page_size: int


class ToApplyJobOut(BaseModel):
    id: int
    company_id: int
    company_name: str
    company_tier: Optional[str] = 'B'
    company_city: Optional[str] = None
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    match_score: float = 0.0
    track: str = 'general'
    track_name: str = '机电综合版'
    recommended_resume: str = '王云鹤_简历_综合.pdf'
    greeting_copy: str = ''
    created_at: Optional[datetime] = None


class SubmissionBase(BaseModel):
    application_id: int
    form_url: str
    prefilled_data: Optional[str] = None
    agent_trace_id: Optional[str] = None
    status: Optional[str] = 'pending_audit'
    screenshot_path: Optional[str] = None
    failure_reason: Optional[str] = None
    resume_used: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    pass

class SubmissionUpdate(BaseModel):
    status: Optional[str] = None
    prefilled_data: Optional[str] = None
    failure_reason: Optional[str] = None
    human_approved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None

class SubmissionOut(SubmissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    human_approved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    application: Optional[ApplicationOut] = None


class InterviewFeedbackBase(BaseModel):
    application_id: int
    interviewer: Optional[str] = None
    interview_date: Optional[datetime] = None
    round: Optional[str] = '一面'
    difficulty: Optional[int] = 3
    self_rating: Optional[int] = 3
    questions: Optional[str] = None
    improvement: Optional[str] = None
    result_status: Optional[str] = '待定'

class InterviewFeedbackCreate(InterviewFeedbackBase):
    pass

class InterviewFeedbackOut(InterviewFeedbackBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


class MemoryBase(BaseModel):
    category: str
    rule_value: Optional[str] = None
    raw_feedback: Optional[str] = None
    weight: Optional[float] = 1.0
    is_active: Optional[bool] = True
    application_id: Optional[int] = None

class MemoryCreate(MemoryBase):
    pass

class MemoryOut(MemoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None


class AutofillRequest(BaseModel):
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    cdp_url: Optional[str] = "http://127.0.0.1:9222"
    resume_track: Optional[str] = "control"

class AutofillResponse(BaseModel):
    success: bool
    platform: str
    filled_fields: int
    prefilled_fields: Dict[str, Any] = {}
    submission_id: Optional[int] = None
    uploaded_resume: Optional[str] = None
    message: str
    zero_submit_safe: bool = True


class TrackMatchRequest(BaseModel):
    job_title: str
    job_description: Optional[str] = ""

class TrackMatchResult(BaseModel):
    track_key: str
    track_name: str
    pdf_name: str
    pdf_path: str
    greeting_template: str
    greeting_copy: str
    highlight_skills: List[str]
    confidence_score: float
