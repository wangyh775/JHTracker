from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    name_alias = Column(String(200), nullable=True)
    tier = Column(String(10), default='B', index=True)  # S/A/B/C
    priority = Column(String(10), default='B', index=True)
    scale = Column(String(50), nullable=True)
    financing_stage = Column(String(50), nullable=True)
    company_type = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    sub_city = Column(String(100), nullable=True)
    address = Column(String(200), nullable=True)
    website = Column(String(500), nullable=True)
    careers_url = Column(String(500), nullable=True)
    source_list = Column(String(100), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    tags = Column(String(500), nullable=True)
    score = Column(Integer, default=0)
    score_reason = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = relationship('Job', back_populates='company', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='company', cascade='all, delete-orphan')
    notes_rel = relationship('Note', back_populates='company', cascade='all, delete-orphan')


class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    salary_range = Column(String(50), nullable=True)
    job_url = Column(String(500), nullable=True)
    job_description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    status = Column(String(20), default='open')
    track = Column(String(30), nullable=True)  # control/embedded_auto/mechatronics/mechanical_cfd
    match_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship('Company', back_populates='jobs')
    applications = relationship('Application', back_populates='job', cascade='all, delete-orphan')


class Resume(Base):
    __tablename__ = 'resumes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), default='pdf')
    file_size = Column(Integer, nullable=True)
    track = Column(String(30), nullable=True)
    note = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship('Application', back_populates='resume')


class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True)
    resume_id = Column(Integer, ForeignKey('resumes.id', ondelete='SET NULL'), nullable=True)
    position = Column(String(200), nullable=False)
    status = Column(String(50), default='待投递')
    channel = Column(String(50), nullable=True)
    track = Column(String(30), default='general')  # control, embedded_auto, mechatronics, mechanical_cfd
    apply_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    resume_version = Column(String(50), default='通用版')
    form_type = Column(String(50), default='structured')  # structured/open_question/attachment/one_click
    source_platform = Column(String(50), nullable=True)  # beisen/moka/nowcoder/zhipin/...
    source_url = Column(String(500), nullable=True)
    match_score = Column(Float, default=0.0)
    scoring_reason = Column(Text, nullable=True)
    agent_reason = Column(Text, nullable=True)
    agent_task_id = Column(String(100), nullable=True)
    feedback = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    offer_salary = Column(String(50), nullable=True)
    offer_status = Column(String(20), nullable=True)
    is_archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship('Company', back_populates='applications')
    job = relationship('Job', back_populates='applications')
    resume = relationship('Resume', back_populates='applications')
    submissions = relationship('ApplicationSubmission', back_populates='application', cascade='all, delete-orphan')
    feedbacks = relationship('InterviewFeedback', back_populates='application', cascade='all, delete-orphan')
    memories = relationship('Memory', back_populates='application', cascade='all, delete-orphan')


class ApplicationSubmission(Base):
    __tablename__ = 'application_submissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    form_url = Column(String(500), nullable=False)
    prefilled_data = Column(Text, nullable=True)  # JSON string of prefilled key-values
    agent_trace_id = Column(String(100), nullable=True)
    status = Column(String(50), default='pending_audit')  # pending_audit/submitted/failed/rejected
    human_approved_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    failure_reason = Column(Text, nullable=True)
    resume_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship('Application', back_populates='submissions')


class InterviewFeedback(Base):
    __tablename__ = 'interview_feedbacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    interviewer = Column(String(100), nullable=True)
    interview_date = Column(DateTime, nullable=True)
    round = Column(String(20), default='一面')  # 一面/二面/终面/HR面
    difficulty = Column(Integer, default=3)  # 1-5
    self_rating = Column(Integer, default=3)  # 1-5
    questions = Column(Text, nullable=True)
    improvement = Column(Text, nullable=True)
    result_status = Column(String(30), default='待定')  # 通过/待定/未通过
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship('Application', back_populates='feedbacks')


class Memory(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='SET NULL'), nullable=True)
    category = Column(String(50), nullable=False)  # exclude_tech, prefer_tech, company_blacklist, etc.
    rule_value = Column(String(200), nullable=True)
    raw_feedback = Column(Text, nullable=True)
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship('Application', back_populates='memories')


class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=True)
    category = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship('Company', back_populates='notes_rel')


class AgentTrace(Base):
    __tablename__ = 'agent_traces'
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
