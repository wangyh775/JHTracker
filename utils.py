"""工具函数：日期解析、整数转换、薪资校验、markdown 表格解析、岗位族归一化。"""
import re
from datetime import datetime


def parse_date(s):
    """解析 YYYY-MM-DD 字符串为 date 对象。空串返回 None，格式错误抛 ValueError。"""
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except ValueError as e:
        raise ValueError(f'日期格式错误: {s!r}，期望 YYYY-MM-DD') from e


def try_int(s, default=None):
    """安全转 int，失败返回 default。"""
    if not s:
        return default
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def validate_salary(min_v, max_v):
    """校验薪资范围。min > max 抛 ValueError。"""
    if min_v is not None and max_v is not None and min_v > max_v:
        raise ValueError(f'薪资下限 {min_v} 不能大于上限 {max_v}')
    return min_v, max_v


def validate_dates(apply_date, deadline):
    """校验日期：截止日期不能早于投递日期。"""
    if apply_date and deadline and deadline < apply_date:
        raise ValueError('截止日期不能早于投递日期')
    return apply_date, deadline


def parse_markdown_table(lines):
    """解析 markdown 表格，返回第一个表格的 (headers, rows)。
    每行是 dict: {header: value}。
    跳过分隔行 |---|---|。
    文件含多张表时仅返回第一张，需遍历所有表请用 parse_all_markdown_tables。
    """
    tables = parse_all_markdown_tables(lines)
    if not tables:
        return [], []
    return tables[0]


def parse_all_markdown_tables(lines):
    """解析 markdown 文件中的所有表格，返回 [(headers, rows), ...]。
    每行是 dict: {header: value}。
    跳过分隔行 |---|---|。文件含多张表时全部返回，调用方可按表头筛选需要的表。
    """
    tables = []
    headers = []
    rows = []
    in_table = False
    for line in lines:
        if '|' not in line:
            if in_table and headers:
                tables.append((headers, rows))
                headers, rows = [], []
                in_table = False
            continue
        parts = [p.strip() for p in line.split('|')]
        # 去掉首尾空元素（split 首尾会产生空串）
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]
        if not parts:
            continue
        # 检测分隔行 |---|---|
        if all(set(p) <= set('-: ') and '-' in p for p in parts):
            continue
        if not headers:
            headers = [p.replace('**', '').strip() for p in parts]
            in_table = True
        else:
            # 表头列数变化 → 视为新表
            if len(parts) != len(headers):
                if headers:
                    tables.append((headers, rows))
                headers = [p.replace('**', '').strip() for p in parts]
                rows = []
                in_table = True
                continue
            rows.append(dict(zip(headers, parts)))
    if in_table and headers:
        tables.append((headers, rows))
    return tables


def safe_filename(name, ext):
    """生成安全存储文件名：{timestamp}_{uuid}.{ext}，避免中文乱码和重名。"""
    import uuid
    return f"{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"


def humanize_size(num_bytes):
    """字节数转人类可读：1.2 MB。"""
    if num_bytes < 1024:
        return f'{num_bytes} B'
    elif num_bytes < 1024 * 1024:
        return f'{num_bytes / 1024:.1f} KB'
    else:
        return f'{num_bytes / (1024 * 1024):.1f} MB'


# 岗位族归一化分隔符候选：全角斜杠、中文顿号、全角顿号、空格
_ROLE_FAMILY_SEP_RE = re.compile(r'[／、,，]|\s+')


def role_family_normalize(text):
    """岗位族归一化：去空格、统一分隔符为半角斜杠、小写。

    用于 AnswerBank/ExperienceBank 唯一键去重，避免「机器人算法」vs「机器人 / 算法」被当两类。

    >>> role_family_normalize('机器人算法')
    '机器人算法'
    >>> role_family_normalize('机器人 / 算法')
    '机器人/算法'
    >>> role_family_normalize('机器人、算法')
    '机器人/算法'
    >>> role_family_normalize('  Embedded  / Software ')
    'embedded/software'
    >>> role_family_normalize(None)
    ''
    """
    if not text:
        return ''
    # 1) 多种分隔符统一为半角斜杠
    s = _ROLE_FAMILY_SEP_RE.sub('/', text.strip())
    # 2) 合并连续斜杠
    s = re.sub(r'/+', '/', s)
    # 3) 去掉首尾斜杠
    s = s.strip('/')
    # 4) 小写（兼容中英混用，对中文无副作用）
    return s.lower()


def role_family_match(stored, queried):
    """判断 stored（库中归一化值）是否匹配 queried（查询归一化值）。

    规则：
    - stored 为空 = 通用，恒匹配；
    - 否则 stored == queried，或 stored 是 queried 的子串（「算法」匹配「算法工程师」）。
    """
    s = role_family_normalize(stored)
    q = role_family_normalize(queried)
    if not s:
        return True  # 通用
    if not q:
        return False  # 查询为空，不匹配任何具体岗位族
    return s == q or s in q or q in s
