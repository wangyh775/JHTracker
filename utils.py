"""工具函数：日期解析、整数转换、薪资校验、markdown 表格解析。"""
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
    """解析 markdown 表格，返回 (headers, rows)。
    每行是 dict: {header: value}。
    跳过分隔行 |---|---|。
    """
    headers = []
    rows = []
    in_table = False
    for line in lines:
        if '|' not in line:
            if in_table and headers:
                break
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
            if len(parts) == len(headers):
                rows.append(dict(zip(headers, parts)))
    return headers, rows


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
