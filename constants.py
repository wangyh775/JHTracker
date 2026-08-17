"""业务常量：状态、行业、城市、徽章颜色、优先级规则。"""

STATUS_LIST = ['待投递', '待提交', '已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer', '已拒']

# 投递前阶段状态（待审批提案、待投递备选、待提交预填区）
# Agent 在此区间内可写：Pending Approval → 待投递 → 待提交
STAGED_STATUS_LIST = ['Pending Approval', '待审批', '待投递', '待提交']

# 投递后流转状态（人类真正提交之后的生命周期状态，Agent 只读保护）
POST_APPLY_STATUS_LIST = ['已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer', '已拒', 'Applied', 'to_apply', 'Rejected', 'rejected']

# 网申预填状态（ApplicationSubmission.status）
SUBMISSION_STATUSES = ['prefilled', 'awaiting_human', 'submitted', 'failed']
SUBMISSION_STATUS_BADGE = {
    'prefilled': 'info',
    'awaiting_human': 'warning',
    'submitted': 'success',
    'failed': 'danger',
}
SUBMISSION_STATUS_LABEL = {
    'prefilled': '已预填',
    'awaiting_human': '待人工处理',
    'submitted': '已提交',
    'failed': '失败',
}

INDUSTRIES = ['3D打印', '机器人', '工业自动化', '高端装备', '汽车制造', '半导体',
              '能源与新能源', '医疗器械', '消费电子', '航空航天', '人工智能/算法',
              '嵌入式/软件', '轨道交通']

CITIES = ['深圳', '上海', '北京', '杭州', '广州', '武汉', '西安', '长沙', '南京', '成都']

STATUS_BADGE = {
    '待投递': 'secondary',
    '待提交': 'primary',
    '已投递': 'info',
    '简历筛选': 'primary',
    '笔试': 'warning',
    '一面': 'warning',
    '二面': 'warning',
    '终面': 'warning',
    'Offer': 'success',
    '已拒': 'danger',
}

# 优先级推断规则：名字包含关键字 → 优先级
PRIORITY_RULES = {
    'S': ['拓竹', 'INTAMSYS', '恒泰'],
    'A': ['创想', '纵维', '智能派', '汇川', '大疆'],
}

# 文件名 → 行业 映射
INDUSTRY_FROM_FILENAME = {
    '医疗': '医疗器械',
    '机器人': '机器人',
    '自动化': '工业自动化',
    '3D': '3D打印',
}

# Offer 状态
OFFER_STATUS_CHOICES = ['pending', 'accepted', 'rejected']
OFFER_STATUS_BADGE = {
    'pending': 'warning',
    'accepted': 'success',
    'rejected': 'secondary',
}
OFFER_STATUS_LABEL = {
    'pending': '待定',
    'accepted': '已接受',
    'rejected': '已拒绝',
}

COMPANY_TYPES = ['民企', '央企', '国企', '合资', '外企-美国', '外企-德国', '外企-日本', '外企-法国', '外企-瑞士', '外企-奥地利', '外企-其他']


SCALE_CHOICES = ['少于50人', '50-200人', '200-1000人', '1000-5000人', '5000人以上']
FINANCING_STAGE_CHOICES = ['未融资', '天使轮', 'A轮', 'B轮', 'C轮', 'D轮及以上', '已上市', '国企', '外企']

# ============================================================
# Safety Guard：网申预填安全边界
# ============================================================
# 敏感字段分类正则：命中后只能从 profile 取，缺失则 awaiting_human，绝不猜测
# (pattern, category) — pattern 大小写不敏感匹配 label/name/id/placeholder
# 分隔符候选：空格 / . / _ / -，统一用 [\W_]* 表示
SENSITIVE_FIELD_PATTERNS = [
    (r'身份证|护照|ssn|id[\W_]*number|national[\W_]*id|身份证号', 'identity'),
    (r'签证|sponsorship|work[\W_]*auth|犯罪|criminal|background[\W_]*check|移民|immigrat|是否需要签证', 'legal'),
    (r'薪资|salary|compensation|expect(ed)?[\W_]*pay|wage|期望薪资|期望薪酬|当前薪资', 'compensation'),
    (r'推荐人|reference|现任雇主|current[\W_]*employ|在职状态|employment[\W_]*status|目前在职', 'current_status'),
    (r'银行|bank[\W_]*account|tax|社保|公积金|银行卡号', 'financial'),
]

# 提交按钮识别：命中以下任一条件视为提交类按钮，Playwright 禁止点击
# 文本正则（长度 ≤ 30 才匹配，避免文章正文误判）
SUBMIT_BUTTON_TEXT_PATTERNS = [
    r'提交', r'确认投递', r'投递简历', r'立即投递', r'申请职位',
    r'apply', r'submit', r'finalize', r'确认申请', r'确认提交',
]

# 提交按钮属性关键词（id/class/type 含任一即视为提交按钮）
SUBMIT_BUTTON_ATTR_KEYWORDS = ['submit', 'confirm', 'apply-button', 'submit-btn', 'apply-btn']

# 预填任务最大耗时（秒）
PLAYWRIGHT_TIMEOUT = 180

# profile.md 中敏感字段对应的标准 key（用于解析 profile 取答案）
PROFILE_SENSITIVE_KEYS = {
    'identity': ['id_card_number', 'passport_number'],
    'legal': ['work_authorization', 'visa_status', 'criminal_record'],
    'compensation': ['target_salary', 'current_salary'],
    'current_status': ['current_employer', 'employment_status', 'references'],
    'financial': ['bank_account', 'social_insurance'],
}

# ============================================================
# Memory Engine：双向偏好规则
# ============================================================
# 正向（approve 产生）：用户偏好/期望
MEMORY_CATEGORIES_POSITIVE = [
    'prefer_tech',       # 偏好技术栈，如 ROS、C++、Python
    'prefer_domain',     # 偏好领域，如 robotics、3d打印
    'prefer_company',    # 偏好公司
    'salary_expected',   # 期望薪资下限
    'culture_fit',       # 文化契合偏好
]
# 负向（reject 产生）：排除规则
MEMORY_CATEGORIES_NEGATIVE = [
    'exclude_tech',      # 排除技术栈
    'exclude_company',   # 排除公司
    'salary_too_low',    # 薪资过低
    'general',           # 通用负向
]
MEMORY_CATEGORIES = MEMORY_CATEGORIES_POSITIVE + MEMORY_CATEGORIES_NEGATIVE
MEMORY_POSITIVE_PREFIX = 'prefer_'


def memory_polarity(category):
    """根据 category 判断极性。返回 'positive' / 'negative'。

    正向规则以 'prefer_' 前缀开头，其余视为负向。
    """
    if category and category.startswith(MEMORY_POSITIVE_PREFIX):
        return 'positive'
    # salary_expected 是正向例外（不以 prefer_ 开头）
    if category == 'salary_expected':
        return 'positive'
    return 'negative'

def infer_priority(name):
    """根据公司名推断优先级，默认 B。"""
    for p, keywords in PRIORITY_RULES.items():
        if any(kw in name for kw in keywords):
            return p
    return 'B'


def infer_industry_from_filename(filename):
    """根据导入文件名推断行业。"""
    for key, ind in INDUSTRY_FROM_FILENAME.items():
        if key in filename:
            return ind
    return '未知'
