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
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=True)  # 关联投递使用的特定简历版本
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
    match_score = db.Column(db.Integer)  # AI 匹配得分 0-100
    agent_reason = db.Column(db.Text)  # AI 推荐理由
    agent_task_id = db.Column(db.String(100))  # 关联抓取任务 ID
    source_url = db.Column(db.String(500))  # 原始岗位链接
    is_archived = db.Column(db.Boolean, default=False, index=True)
    archived_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    feedbacks = db.relationship('InterviewFeedback', backref='application',
                                cascade='all,delete-orphan', lazy='dynamic')
    decision_feedbacks = db.relationship('DecisionFeedback', backref='application',
                                         cascade='all,delete-orphan', lazy='dynamic')
    memories = db.relationship('Memory', backref='application', cascade='all,delete-orphan', lazy='dynamic')
    submissions = db.relationship('ApplicationSubmission', backref='application',
                                  cascade='all,delete-orphan', lazy='dynamic')
    resume = db.relationship('Resume', backref='applications', lazy='select')


class Memory(db.Model):
    __tablename__ = 'memories'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=True)
    # 双向偏好规则：正向 prefer_* / salary_expected（approve 产生），负向 exclude_* / salary_too_low / general（reject 产生）
    # 详见 constants.MEMORY_CATEGORIES 与 constants.memory_polarity()
    category = db.Column(db.String(50), nullable=False)
    # 结构化值（如 ROS、外包、15000）；可为空，由批量归纳脚本补齐；不应存长文本反馈
    rule_value = db.Column(db.String(200))
    # 人类原始评语（approve/reject 均可），自由文本
    raw_feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)



class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    category = db.Column(db.String(50))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
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
    pdf_path = db.Column(db.String(500))  # LibreOffice 转换的 PDF 预览路径（DOCX 才有）
    created_at = db.Column(db.DateTime, default=datetime.now)


class AgentTask(db.Model):
    __tablename__ = 'agent_tasks'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    agent_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='running')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    events = db.relationship('AgentEvent', backref='task', lazy='dynamic', cascade='all,delete-orphan')


class AgentEvent(db.Model):
    __tablename__ = 'agent_events'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('agent_tasks.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    payload_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class DecisionFeedback(db.Model):
    __tablename__ = 'decision_feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # approve, reject, edit
    reason_category = db.Column(db.String(50))  # tech_mismatch, salary_low, company_reputation, location, general
    raw_feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class AnswerBank(db.Model):
    """可复用求职答案库。敏感答案（身份/法律/薪酬等）不入库，从 data/profile.md 直通。"""
    __tablename__ = 'answer_bank'
    id = db.Column(db.Integer, primary_key=True)
    question_pattern = db.Column(db.String(200), nullable=False, index=True)  # 问题模式（子串或正则）
    answer = db.Column(db.Text, nullable=False)
    role_family = db.Column(db.String(100), index=True)  # 岗位族，空=通用；入库前需经 role_family_normalize
    needs_review = db.Column(db.Boolean, default=False)  # True=人工确认后才参与自动填
    source = db.Column(db.String(20), default='manual')  # manual / extracted
    created_at = db.Column(db.DateTime, default=datetime.now)


class ExperienceBank(db.Model):
    """按岗位族路由的经历片段库，供 get_resume_for_role 选最佳简历与经历组合。"""
    __tablename__ = 'experience_bank'
    id = db.Column(db.Integer, primary_key=True)
    role_family = db.Column(db.String(100), nullable=False, index=True)
    bullet_text = db.Column(db.Text, nullable=False)
    jd_keywords = db.Column(db.String(500))  # 命中哪些 JD 关键词时优先用，逗号分隔
    priority = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)


class ApplicationSubmission(db.Model):
    """网申预填执行记录。Agent 预填后状态=待提交，人类在真实页面提交后回写已投递。"""
    __tablename__ = 'application_submissions'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False, index=True)
    form_url = db.Column(db.String(500), nullable=False)
    prefilled_data = db.Column(db.Text)  # JSON，结构见 design.md Decision #4
    agent_trace_id = db.Column(db.String(100))
    status = db.Column(db.String(50), default='prefilled')  # prefilled/awaiting_human/submitted/failed
    human_approved_at = db.Column(db.DateTime)
    submitted_at = db.Column(db.DateTime)
    screenshot_path = db.Column(db.String(500))
    failure_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


