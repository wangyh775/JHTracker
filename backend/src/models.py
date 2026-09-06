from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class JobItem(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str] = None
    industry: Optional[str] = None
    type_tags: Optional[List[str]] = Field(default_factory=list)
    batch: Optional[str] = None
    education_req: Optional[str] = None
    target_grad_year: Optional[List[str]] = Field(default_factory=list)
    salary_range: Optional[str] = None
    publish_date: str
    deadline: Optional[str] = None
    detail_url: Optional[str] = None
    referral_code: Optional[str] = None
    description: Optional[str] = None
    source_site: str = "default"
    popular_level: int = 1
    category: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class JobSearchQuery(BaseModel):
    keyword: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    type_tags: Optional[List[str]] = None
    batch: Optional[str] = None
    education_req: Optional[str] = None
    target_grad_year: Optional[str] = None
    category: Optional[str] = None
    has_referral: Optional[bool] = None
    city: Optional[str] = None
    # Flexible time constraint parameters
    since_date: Optional[str] = None  # e.g. "2026-09-01"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    time_window_months: Optional[int] = None # e.g. 3
    limit: int = 50
    offset: int = 0

class RecommendationQuery(BaseModel):
    resume_id: Optional[str] = None
    resume_text: Optional[str] = None
    min_match_score: float = 0.60
    since_date: Optional[str] = None
    time_window_months: Optional[int] = 3
    limit: int = 20

class RecommendationItem(BaseModel):
    job: JobItem
    raw_match_score: float
    adjusted_score: float
    recommend_reason: str
    feature_breakdown: Dict[str, Any] = Field(default_factory=dict)

class FeedbackRequest(BaseModel):
    job_id: str
    action: str  # "ACCEPT" | "REJECT"
    reject_reasons: Optional[List[str]] = Field(default_factory=list)
    match_score: Optional[float] = None
    recommend_reason: Optional[str] = None

class ApplicationItem(BaseModel):
    id: str
    job_id: Optional[str] = None
    company: str
    title: str
    resume_id: Optional[str] = None
    status: str = "PENDING_APPLY"
    apply_date: Optional[str] = None
    schedule_time: Optional[str] = None
    channel: Optional[str] = None
    account_memo: Optional[str] = None
    interview_notes: Optional[str] = None
    salary_offered: Optional[str] = None
    priority: int = 0
    updated_at: Optional[str] = None
    # 关联岗位详细属性（展示层自动填充）
    location: Optional[str] = None
    industry: Optional[str] = None
    type_tags: Optional[List[str]] = Field(default_factory=list)
    salary_range: Optional[str] = None
    education_req: Optional[str] = None
    batch: Optional[str] = None
    detail_url: Optional[str] = None
    apply_url: Optional[str] = None
    description: Optional[str] = None
    match_score: Optional[float] = None
    recommend_reason: Optional[str] = None
    is_archived: bool = False

class KeywordItem(BaseModel):
    keyword: str
    weight: float = 1.0
    source: Optional[str] = ""
    enabled: bool = True

class KeywordCategories(BaseModel):
    core: List[KeywordItem] = Field(default_factory=list)
    domain: List[KeywordItem] = Field(default_factory=list)
    base: List[KeywordItem] = Field(default_factory=list)
    negative: List[KeywordItem] = Field(default_factory=list)

# Alias for compatibility
KeywordMatrixCategories = KeywordCategories

class KeywordMatrix(BaseModel):
    version: int = 1
    updated_at: Optional[str] = None
    updated_by: str = "AGENT_INIT"  # "AGENT_INIT" | "USER_MANUAL" | "AUTO_EXTRACT"
    categories: KeywordCategories = Field(default_factory=KeywordCategories)

class ResumeItem(BaseModel):
    id: str
    title: str
    category: str = "GENERAL"  # "GENERAL" | "CUSTOMIZED"
    file_path: Optional[str] = ""
    content_md: Optional[str] = None
    target_job_id: Optional[str] = None
    parsed_skills: Optional[List[str]] = Field(default_factory=list)
    keywords_matrix: Optional[KeywordMatrix] = None
    is_default: bool = False
    version_type: str = "ORIGINAL"  # "ORIGINAL" | "AI_OPTIMIZED"
    parent_resume_id: Optional[str] = None  # 关联的原始简历 ID (针对 AI 优化版)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ResumeUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content_md: Optional[str] = None
    content_markdown: Optional[str] = None
    parsed_skills: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    is_default: Optional[bool] = None
    version_type: Optional[str] = None
    parent_resume_id: Optional[str] = None
    keywords_matrix: Optional[KeywordMatrix] = None

class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None
    schedule_time: Optional[str] = None

class ArchiveUpdateRequest(BaseModel):
    is_archived: bool

class LLMConfig(BaseModel):
    base_url: str = "http://127.0.0.1:8045/v1"
    api_key: Optional[str] = ""
    model: str = "claude-3-5-sonnet-20241022"
    temperature: Optional[float] = 0.3

class ResumeOptimizeRequest(BaseModel):
    job_id: Optional[str] = None
    job_description: Optional[str] = None
    resume_id: Optional[str] = None
    resume_content_md: Optional[str] = None
    mode: str = "GENERAL"  # "GENERAL" (通用) | "TARGETED" (专岗) | "CUSTOMIZED" (兼容旧参数)
    target_company: Optional[str] = None  # 专岗-目标企业 (如: "腾讯")
    target_position: Optional[str] = None # 专岗-目标岗位 (如: "前端开发")
    engine: str = "auto"                  # "auto" | "custom_api" | "opencode" | "hermes" | "builtin"
    save_as_version: bool = False         # 是否保存为独立的 AI 优化版本简历记录 (不覆写原始简历)
    llm_config: Optional[LLMConfig] = None # 用户自定义/本地 OpenAI 兼容端点配置

class AgentPushItem(BaseModel):
    id: str
    job_id: str
    agent_name: str = "JobSourcingAgent"
    recommend_reason: str
    match_score: float = 0.95
    pushed_at: Optional[str] = None
    job: Optional[JobItem] = None

class AgentPushCreate(BaseModel):
    job_id: str
    agent_name: str = "JobSourcingAgent"
    recommend_reason: str
    match_score: float = 0.95
