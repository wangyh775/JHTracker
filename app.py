"""Job Hunt Tracker — 求职全流程管理工具"""
import json, os, re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import atexit
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'data', 'tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'jobhunt-tracker-2026-secret'
db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────────────

class Company(db.Model):
    __tablename__ = 'companies'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False, index=True)
    industry    = db.Column(db.String(100))       # 工业自动化/机器人/3D打印/能源/半导体/汽车/医疗/消费电子/高端装备
    city        = db.Column(db.String(100))       # 北京/上海/广州/深圳/杭州
    sub_city    = db.Column(db.String(100))       # 具体区/街道
    job_type    = db.Column(db.String(100))       # 岗位方向
    match_reason = db.Column(db.Text)             # 匹配理由
    priority    = db.Column(db.String(4))         # S/A/B/C
    website     = db.Column(db.String(500))       # 官网
    source_list = db.Column(db.String(100))       # 来源清单
    created_at  = db.Column(db.DateTime, default=datetime.now)

    applications = db.relationship('Application', backref='company', lazy='dynamic', cascade='all,delete-orphan')
    notes       = db.relationship('Note', backref='company', lazy='dynamic', cascade='all,delete-orphan')

class Application(db.Model):
    __tablename__ = 'applications'
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    position    = db.Column(db.String(200))       # 岗位名称
    channel     = db.Column(db.String(50))        # BOSS直聘/猎聘/官网/内推/领英/邮箱
    status      = db.Column(db.String(50), default='待投递')  # 待投递→已投递→简历筛选→笔试→一面→二面→终面→Offer→已拒
    apply_date  = db.Column(db.Date)
    deadline    = db.Column(db.Date)              # 投递截止
    salary_min  = db.Column(db.Integer)           # 薪资范围下限 k/月
    salary_max  = db.Column(db.Integer)           # 薪资范围上限 k/月
    job_desc    = db.Column(db.Text)              # JD原文
    url         = db.Column(db.String(500))       # 投递链接
    feedback    = db.Column(db.Text)              # 反馈记录
    created_at  = db.Column(db.DateTime, default=datetime.now)
    updated_at  = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Note(db.Model):
    __tablename__ = 'notes'
    id          = db.Column(db.Integer, primary_key=True)
    company_id  = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    category    = db.Column(db.String(50))        # interview/reflection/company_note/other
    title       = db.Column(db.String(200))
    content     = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.now)

class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200))
    category    = db.Column(db.String(50))        # control/mechanical/sensor/motor/embedded/plc/thermal/behavior/coding
    subcategory = db.Column(db.String(100))
    source_file = db.Column(db.String(200))       # 源文件路径
    summary     = db.Column(db.Text)
    is_learned  = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.now)

class Timeline(db.Model):
    __tablename__ = 'timeline'
    id          = db.Column(db.Integer, primary_key=True)
    event_date  = db.Column(db.Date, nullable=False)
    title       = db.Column(db.String(200))
    description = db.Column(db.Text)
    event_type  = db.Column(db.String(50))        # deadline/action/reminder/milestone
    done        = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.now)

# ── helpers ────────────────────────────────────────────────────────────────

def status_weight(s):
    return {'待投递':0,'已投递':1,'简历筛选':2,'笔试':3,'一面':4,'二面':5,'终面':6,'Offer':7,'已拒':-1}.get(s, 0)

STATUS_LIST = ['待投递','已投递','简历筛选','笔试','一面','二面','终面','Offer','已拒']

INDUSTRIES = ['3D打印','机器人','工业自动化','高端装备','汽车制造','半导体设备',
              '能源与新能源','医疗器械','消费电子','航空航天','人工智能']

CITIES = ['深圳','上海','北京','杭州','广州','武汉','西安','长沙','南京','成都']

STATUS_BADGE = {
    '待投递':'secondary','已投递':'info','简历筛选':'primary','笔试':'warning',
    '一面':'warning','二面':'warning','终面':'warning','Offer':'success','已拒':'danger'
}

@app.context_processor
def inject_globals():
    return dict(status_list=STATUS_LIST, industries=INDUSTRIES, cities=CITIES, status_badge=STATUS_BADGE, now=datetime.now)

# ── Routes ────────────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    total = Company.query.count()
    applied = Application.query.filter(Application.status.in_(['已投递','简历筛选','笔试','一面','二面','终面','Offer'])).count()
    interviews = Application.query.filter(Application.status.in_(['一面','二面','终面'])).count()
    offers = Application.query.filter_by(status='Offer').count()
    rejected = Application.query.filter_by(status='已拒').count()

    # funnel
    status_counts = db.session.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    funnel = {s:0 for s in STATUS_LIST}
    for s,c in status_counts:
        funnel[s]=c

    # city distribution
    city_counts = db.session.query(Company.city, func.count(Company.id)).filter(Company.city!='').group_by(Company.city).all()

    # industry distribution
    ind_counts = db.session.query(Company.industry, func.count(Company.id)).filter(Company.industry!='').group_by(Company.industry).all()

    # priority breakdown
    pri_counts = db.session.query(Company.priority, func.count(Company.id)).filter(Company.priority!='').group_by(Company.priority).all()

    # timeline upcoming
    upcoming = Timeline.query.filter(Timeline.done==False).order_by(Timeline.event_date).limit(5).all()

    recent = Application.query.order_by(Application.updated_at.desc()).limit(5).all()

    max_funnel = max(funnel.values()) if funnel.values() else 1

    return render_template('dashboard.html',
        total=total, applied=applied, interviews=interviews, offers=offers, rejected=rejected,
        funnel=funnel, max_funnel=max_funnel, city_counts=city_counts, ind_counts=ind_counts, pri_counts=pri_counts,
        upcoming=upcoming, recent=recent)

# ── Companies ──────────────────────────────────────────────────────────────

@app.route('/companies')
def company_list():
    page = request.args.get('page',1,type=int)
    ind = request.args.get('industry','')
    ct = request.args.get('city','')
    pr = request.args.get('priority','')
    q = request.args.get('q','')

    query = Company.query
    if ind: query = query.filter_by(industry=ind)
    if ct:  query = query.filter(Company.city.contains(ct))
    if pr:  query = query.filter_by(priority=pr)
    if q:   query = query.filter(Company.name.contains(q) | Company.match_reason.contains(q))

    companies = query.order_by(Company.priority, Company.name).paginate(page=page, per_page=40)
    return render_template('companies.html', companies=companies)

@app.route('/companies/<int:c_id>')
def company_detail(c_id):
    c = Company.query.get_or_404(c_id)
    apps = c.applications.order_by(Application.updated_at.desc()).all()
    notes = c.notes.order_by(Note.created_at.desc()).all()
    return render_template('company_detail.html', company=c, apps=apps, notes=notes)

@app.route('/companies/add', methods=['POST'])
def company_add():
    c = Company(
        name=request.form['name'],
        industry=request.form.get('industry',''),
        city=request.form.get('city',''),
        sub_city=request.form.get('sub_city',''),
        job_type=request.form.get('job_type',''),
        match_reason=request.form.get('match_reason',''),
        priority=request.form.get('priority','B'),
        website=request.form.get('website',''),
        source_list=request.form.get('source_list',''),
    )
    db.session.add(c)
    db.session.commit()
    return redirect(url_for('company_list'))

@app.route('/companies/<int:c_id>/edit', methods=['POST'])
def company_edit(c_id):
    c = Company.query.get_or_404(c_id)
    c.name = request.form.get('name',c.name)
    c.industry = request.form.get('industry',c.industry)
    c.city = request.form.get('city',c.city)
    c.sub_city = request.form.get('sub_city',c.sub_city)
    c.job_type = request.form.get('job_type',c.job_type)
    c.match_reason = request.form.get('match_reason',c.match_reason)
    c.priority = request.form.get('priority',c.priority)
    c.website = request.form.get('website',c.website)
    db.session.commit()
    return redirect(url_for('company_detail', c_id=c_id))

@app.route('/companies/<int:c_id>/delete', methods=['POST'])
def company_delete(c_id):
    c = Company.query.get_or_404(c_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('company_list'))

# ── Applications ──────────────────────────────────────────────────────────

@app.route('/applications')
def app_list():
    page = request.args.get('page',1,type=int)
    st = request.args.get('status','')
    ch = request.args.get('channel','')
    query = Application.query
    if st: query = query.filter_by(status=st)
    if ch: query = query.filter_by(channel=ch)
    apps = query.order_by(Application.updated_at.desc()).paginate(page=page, per_page=30)
    channels = db.session.query(Application.channel, func.count(Application.id)).group_by(Application.channel).all()
    return render_template('applications.html', apps=apps, channels=channels)

@app.route('/applications/add', methods=['POST'])
def app_add():
    a = Application(
        company_id=request.form['company_id'],
        position=request.form.get('position',''),
        channel=request.form.get('channel',''),
        status=request.form.get('status','待投递'),
        apply_date=parse_date(request.form.get('apply_date','')),
        deadline=parse_date(request.form.get('deadline','')),
        salary_min=try_int(request.form.get('salary_min')),
        salary_max=try_int(request.form.get('salary_max')),
        job_desc=request.form.get('job_desc',''),
        url=request.form.get('url',''),
    )
    db.session.add(a)
    db.session.commit()
    return redirect(request.referrer or url_for('app_list'))

@app.route('/applications/<int:a_id>/status', methods=['POST'])
def app_status(a_id):
    a = Application.query.get_or_404(a_id)
    a.status = request.form['status']
    if 'feedback' in request.form:
        a.feedback = request.form['feedback']
    db.session.commit()
    return redirect(request.referrer or url_for('app_list'))

@app.route('/applications/<int:a_id>/delete', methods=['POST'])
def app_delete(a_id):
    a = Application.query.get_or_404(a_id)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for('app_list'))

# ── Notes ──────────────────────────────────────────────────────────────────

@app.route('/notes', methods=['GET','POST'])
def notes():
    if request.method == 'POST':
        n = Note(
            company_id=try_int(request.form.get('company_id')) or None,
            category=request.form.get('category','other'),
            title=request.form['title'],
            content=request.form.get('content',''),
        )
        db.session.add(n)
        db.session.commit()
        return redirect(url_for('notes'))
    page = request.args.get('page',1,type=int)
    ns = Note.query.order_by(Note.created_at.desc()).paginate(page=page, per_page=30)
    return render_template('notes.html', notes=ns)

@app.route('/notes/<int:n_id>/delete', methods=['POST'])
def note_delete(n_id):
    n = Note.query.get_or_404(n_id)
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for('notes'))

# ── Study ──────────────────────────────────────────────────────────────────

@app.route('/study')
def study_list():
    cat = request.args.get('category','')
    query = StudyMaterial.query
    if cat: query = query.filter_by(category=cat)
    mats = query.order_by(StudyMaterial.category, StudyMaterial.title).all()
    return render_template('study.html', materials=mats)

@app.route('/study/<int:m_id>/content')
def study_content(m_id):
    m = StudyMaterial.query.get_or_404(m_id)
    try:
        with open(m.source_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        content = f"无法读取文件 {m.source_file}: {str(e)}"
    
    # 简单提取对应章节（如果不想要全量也可以，这里先传全量或者尝试按标题切割）
    # 为简单起见，这里直接把整个 md 传给前端，前端可以用 marked.js 渲染
    return render_template('study_content.html', material=m, content=content)

@app.route('/study/<int:m_id>/toggle', methods=['POST'])
def study_toggle(m_id):
    m = StudyMaterial.query.get_or_404(m_id)
    m.is_learned = not m.is_learned
    db.session.commit()
    return redirect(url_for('study_list'))

# ── Timeline ────────────────────────────────────────────────────────────────

@app.route('/timeline')
def timeline_view():
    items = Timeline.query.order_by(Timeline.event_date, Timeline.id).all()
    return render_template('timeline.html', items=items)

@app.route('/timeline/add', methods=['POST'])
def timeline_add():
    t = Timeline(
        event_date=parse_date(request.form['event_date']),
        title=request.form['title'],
        description=request.form.get('description',''),
        event_type=request.form.get('event_type','action'),
    )
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('timeline_view'))

@app.route('/timeline/<int:t_id>/toggle', methods=['POST'])
def timeline_toggle(t_id):
    t = Timeline.query.get_or_404(t_id)
    t.done = not t.done
    db.session.commit()
    return redirect(url_for('timeline_view'))

# ── Import ──────────────────────────────────────────────────────────────────

@app.route('/import')
def import_page():
    return render_template('import.html')

@app.route('/import/companies', methods=['POST'])
def import_companies():
    """从 career/ 目录的 Markdown 清单批量导入公司"""
    source = request.form.get('source','A')
    path = f"D:/DJTU/HermesWorkspace/career/企业清单_{source}_*.md"
    import glob, re
    files = glob.glob(path)
    if not files:
        files = glob.glob("D:/DJTU/HermesWorkspace/career/*.md")
        files = [f for f in files if '企业清单' in f]
    count = 0
    for fp in files:
        with open(fp, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        current = {}
        for line in lines:
            if '|' not in line:
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                # [ '', '1', '拓竹科技', '深圳', '机械结构工程师', '匹配理由', '' ]
                name_idx = 2 if parts[1].isdigit() or parts[1] == '排名' else 1
                if '公司' in parts[name_idx] or '---' in parts[name_idx]:
                    continue
                    
                name = parts[name_idx]
                if name:
                    # Clean markdown bold **
                    name = name.replace('**','').strip()
                    existing = Company.query.filter_by(name=name).first()
                    if not existing:
                        priority = 'B'
                        if '拓竹' in name or 'INTAMSYS' in name or '恒泰' in name:
                            priority = 'S'
                        elif '创想' in name or '纵维' in name or '智能派' in name or '汇川' in name or '大疆' in name:
                            priority = 'A'
                            
                        # find columns based on headers if possible, or fallback
                        industry = '未知'
                        if '医疗' in fp: industry = '医疗器械'
                        elif '机器人' in fp: industry = '机器人'
                        elif '自动化' in fp: industry = '工业自动化'
                        elif '3D' in fp: industry = '3D打印'
                        
                        c = Company(name=name, industry=industry, city=parts[name_idx+1],
                                   job_type=parts[name_idx+2], match_reason=parts[name_idx+3], priority=priority,
                                   source_list=f"清单{source}")
                        db.session.add(c)
                        count += 1
        db.session.commit()
    return redirect(url_for('company_list'))

@app.route('/import/study', methods=['POST'])
def import_study():
    """从面试复习手册导入科目分类"""
    path = "D:/DJTU/HermesWorkspace/career/面试复习手册_自动化机电工程师.md"
    cats = {
        '自动控制原理':'control','机械设计基础':'mechanical','传感器与检测技术':'sensor',
        '电机与运动控制':'motor','嵌入式与编程':'embedded','PLC与工业网络':'plc',
        '热工基础':'thermal','面试行为问题':'behavior'
    }
    try:
        with open(path,'r',encoding='utf-8') as f:
            content = f.read()
        for cn, cat in cats.items():
            existing = StudyMaterial.query.filter_by(category=cat).first()
            if not existing:
                sm = StudyMaterial(title=f"面试复习——{cn}", category=cat,
                                  source_file=path, summary=f"自动导入：{cn}", is_learned=False)
                db.session.add(sm)
        db.session.commit()
    except: pass

    # also import coding problems
    path2 = "D:/DJTU/HermesWorkspace/career/面试编程题.md"
    try:
        with open(path2,'r',encoding='utf-8') as f:
            content = f.read()
        existing = StudyMaterial.query.filter_by(category='coding').first()
        if not existing:
            sm = StudyMaterial(title="面试编程题集（12题）", category='coding',
                              source_file=path2, summary="自动导入：PID仿真、串口通信、运动控制等", is_learned=False)
            db.session.add(sm)
            db.session.commit()
    except: pass

    return redirect(url_for('study_list'))

@app.route('/import/timeline', methods=['POST'])
def import_timeline():
    """添加秋招关键节点"""
    nodes = [
        ('2026-07-25','秋招正式启动','开始大规模投递，完成简历优化','action'),
        ('2026-08-15','拓竹提前批截止','确认投递状态','deadline'),
        ('2026-09-01','秋招正式批高峰','全面铺开投递，预计每日投3-5家','action'),
        ('2026-09-15','面试高发期','大量笔试/一面','milestone'),
        ('2026-10-15','大论文初稿完成','毕业论文主体完成，腾出精力面试','milestone'),
        ('2026-10-31','秋招投递截止','大部分公司秋招网申截止','deadline'),
        ('2026-11-15','Offer决策期','评估所有offer，做最终决定','milestone'),
        ('2026-12-01','毕业论文定稿','修改完善论文准备答辩','deadline'),
        ('2027-03-01','春招启动','如秋招未果，春招补充','action'),
    ]
    for dt,title,desc,typ in nodes:
        existing = Timeline.query.filter_by(title=title).first()
        if not existing:
            t = Timeline(event_date=parse_date(dt), title=title, description=desc, event_type=typ)
            db.session.add(t)
    db.session.commit()
    return redirect(url_for('timeline_view'))

# ── API ──────────────────────────────────────────────────────────────────────

@app.route('/api/stats')
def api_stats():
    total = Company.query.count()
    apps = Application.query.count()
    offers = Application.query.filter_by(status='Offer').count()
    interviews = Application.query.filter(Application.status.in_(['一面','二面','终面'])).count()
    return jsonify(total=total, applications=apps, offers=offers, interviews=interviews)

@app.route('/api/companies/search')
def api_company_search():
    q = request.args.get('q','')
    if not q: return jsonify([])
    cs = Company.query.filter(Company.name.contains(q)).limit(10).all()
    return jsonify([{'id':c.id,'name':c.name,'city':c.city,'industry':c.industry} for c in cs])

# ── Utils ──────────────────────────────────────────────────────────────────

def parse_date(s):
    if not s: return None
    try: return datetime.strptime(s[:10],'%Y-%m-%d').date()
    except: return None

def try_int(s, default=None):
    if not s: return default
    try: return int(s)
    except: return default

# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
