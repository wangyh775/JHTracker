export interface JobItem {
  id: string;
  title: string;
  company: string;
  location?: string;
  city?: string;
  industry?: string;
  batch?: string;
  salary_range?: string;
  publish_date?: string;
  deadline?: string;
  description?: string;
  description_raw?: string;
  source_site?: string;
  detail_url?: string;
  apply_url?: string;
  application_link?: string;
  source_url?: string;
  skills_required?: string[];
  type_tags?: string[];
  referral_code?: string;
  popular_level?: number;
  category?: 'latest' | 'hot' | 'campus' | 'state_owned' | 'intern' | 'all' | string;
}

export type FangzhouCategory = 'latest' | 'hot' | 'campus' | 'state_owned' | 'intern' | 'all';
export type CategoryTab = 'latest' | 'hot' | 'campus' | 'state_owned' | 'intern' | 'all';

export interface TableFilterState {
  category: CategoryTab;
  city: string;
  batch: string;
  hasReferral: boolean;
  searchKeyword: string;
  hideVisited: boolean;
  timeWindowDays: number;
}

export interface VisitedRecord {
  jobId: string;
  visitedAt: string;
  action: 'detail' | 'apply' | 'referral';
}

export type VisitedRecordMap = Record<string, VisitedRecord>;

export type ApplicationStatus = 'PENDING_APPLY' | 'APPLIED' | 'OA_SCREENING' | 'INTERVIEW_STAGE' | 'OFFER_RECEIVED' | 'REJECTED';

export interface ApplicationItem {
  id: string;
  job_id?: string;
  company: string;
  title: string;
  status: ApplicationStatus;
  channel?: string;
  applied_at?: string;
  apply_date?: string;
  interview_time?: string;
  schedule_time?: string;
  notes?: string;
  interview_notes?: string;
  salary_offered?: string;
  priority?: number;
  // 关联岗位全量详情
  location?: string;
  industry?: string;
  type_tags?: string[];
  salary_range?: string;
  education_req?: string;
  batch?: string;
  detail_url?: string;
  apply_url?: string;
  description?: string;
  match_score?: number;
  recommend_reason?: string;
  is_archived?: boolean;
}

export interface RecommendationItem {
  job: JobItem;
  score?: number;
  match_score?: number;
  reason?: string;
  recommend_reason?: string;
}

export interface ResumeItem {
  id: string;
  title: string;
  skills?: string[];
  content_markdown: string;
  category?: 'GENERAL' | 'CUSTOMIZED' | string;
  target_job_id?: string;
  is_default?: boolean;
  version_type?: 'ORIGINAL' | 'AI_OPTIMIZED' | string;
  parent_resume_id?: string;
  updated_at?: string;
}

export interface ParseResumeResponse {
  title: string;
  content_markdown: string;
  skills: string[];
  filename?: string;
  file_size?: number;
}

export interface AgentPushItem {
  id: string;
  job_id: string;
  agent_name: string;
  recommend_reason: string;
  match_score: number;
  pushed_at?: string;
  job?: JobItem;
}
