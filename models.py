"""ORM 模型定义。"""
from datetime import datetime
from extensions import db


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    industry = db.Column(db.String(100))
    city = db.Column(db.String(100))
    sub_city = db.Column(db.String(100))
    job_type = db.Column(db.String(100))
    match_reason = db.Column(db.Text)
    priority = db.Column(db.String(4), index=True)  # S/A/B/C
    website = db.Column(db.String(500))
    source_list = db.Column(db.String(100))
    salary_min = db.Column(db.Integer)  # 公司级参考薪资下限 k/月
    salary_max = db.Column(db.Integer)  # 公司级参考薪资上限 k/月
    scale = db.Column(db.String(50))  # 规模：少于50人/50-200人/200-1000人/1000-5000人/5000人以上
    financing_stage = db.Column(db.String(50))  # 融资阶段：未融资/天使轮/A轮/B轮/C轮/D轮及以上/已上市/国企
    tags = db.Column(db.String(500))  # 自定义标签，逗号分隔，如"内推,已联系HR,面试中"
    company_type = db.Column(db.String(50))  # 企业性质：民企/央企/国企/合资/外企-XX
    score = db.Column(db.Integer)  # AI 匹配评分 0-100
    score_reason = db.Column(db.String(500))  # AI 评分理由
    created_at = db.Column(db.DateTime, default=datetime.now)

    applications = db.relationship('Application', backref='company', lazy='dynamic', cascade='all,delete-orphan')
    notes = db.relationship('Note', backref='company', lazy='dynamic', cascade='all,delete-orphan')


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    position = db.Column(db.String(200))
    channel = db.Column(db.String(50))
    status = db.Column(db.String(50), default='待投递')
    apply_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    salary_min = db.Column(db.Integer)  # 投递时具体薪资下限
    salary_max = db.Column(db.Integer)
    job_desc = db.Column(db.Text)
    url = db.Column(db.String(500))
    feedback = db.Column(db.Text)
    offer_status = db.Column(db.String(20))  # pending/accepted/rejected，仅 status=Offer 时有意义
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    feedbacks = db.relationship('InterviewFeedback', backref='application',
                                cascade='all,delete-orphan', lazy='dynamic')


class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    category = db.Column(db.String(50))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(100))
    source_file = db.Column(db.String(200))
    summary = db.Column(db.Text)
    is_learned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Timeline(db.Model):
    __tablename__ = 'timeline'
    id = db.Column(db.Integer, primary_key=True)
    event_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # 甘特图结束日期，NULL 时等于 event_date
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class InterviewFeedback(db.Model):
    __tablename__ = 'interview_feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    interviewer = db.Column(db.String(100))
    interview_date = db.Column(db.Date)
    round = db.Column(db.String(20))  # 一面/二面/终面
    difficulty = db.Column(db.Integer)  # 1-5
    self_rating = db.Column(db.Integer)  # 1-5
    questions = db.Column(db.Text)
    improvement = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    version = db.Column(db.String(50))
    file_path = db.Column(db.String(500), nullable=False)  # 相对路径 data/resumes/xxx.pdf
    file_type = db.Column(db.String(10))  # pdf / docx
    file_size = db.Column(db.Integer)
    note = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
