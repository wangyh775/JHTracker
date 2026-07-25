"""业务常量：状态、行业、城市、徽章颜色、优先级规则。"""

STATUS_LIST = ['待投递', '已投递', '简历筛选', '笔试', '一面', '二面', '终面', 'Offer', '已拒']

INDUSTRIES = ['3D打印', '机器人', '工业自动化', '高端装备', '汽车制造', '半导体设备',
              '能源与新能源', '医疗器械', '消费电子', '航空航天', '人工智能']

CITIES = ['深圳', '上海', '北京', '杭州', '广州', '武汉', '西安', '长沙', '南京', '成都']

STATUS_BADGE = {
    '待投递': 'secondary',
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
