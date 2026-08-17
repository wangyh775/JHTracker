"""国内 ATS 平台直连岗位检索（Layer 0）。

封装北森（Beisen）、Moka、牛客网、应届生求职网 4 家 ATS 的公开 JSON 接口，
对 Agent 屏蔽各平台接口差异，返回标准化 AtsJob 结构。

作为分层检索协议的 Layer 0（最优先层），校招场景下应优先调用，
命中 ≥3 条结果即可停止检索，避免进入高风险的 CDP 层。

参考：
- openspec/changes/cn-sourcing-ats-first/design.md
- openspec/specs/cn-ats-sourcing/spec.md
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from typing import List, Optional
from urllib import error, parse, request


# 各 ATS 接口超时（秒）
ATS_TIMEOUT = 10

# 公开 AppId（北森，从任意北森招聘页可抓取的公开值）
BEISEN_APP_ID = '11001'


# ============================================================
# 标准化 Job 结构
# ============================================================
@dataclass
class AtsJob:
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    apply_url: Optional[str] = None
    form_type: str = 'open_question'  # structured/open_question/attachment/one_click
    source_platform: str = ''          # beisen/moka/nowcoder/yingjiesheng
    raw: dict = field(default_factory=dict)


# ============================================================
# form_type 识别规则（按 apply_url 域名匹配）
# ============================================================
# (pattern, form_type) — 大小写不敏感
FORM_TYPE_RULES = [
    (r'beisen\.com|yingjiesheng\.com', 'structured'),
    (r'mokahr\.com', 'structured'),
    (r'nowcoder\.com', 'structured'),
    (r'workday\.com|myworkdayjobs\.com', 'attachment'),
    (r'greenhouse\.io|lever\.co', 'attachment'),
    (r'zhipin\.com', 'one_click'),
]


def identify_form_type(apply_url: str) -> str:
    """按 apply_url 域名匹配 form_type 规则，未命中返回 open_question（最保守）。"""
    if not apply_url:
        return 'open_question'
    url_lower = apply_url.lower()
    for pattern, form_type in FORM_TYPE_RULES:
        if re.search(pattern, url_lower):
            return form_type
    return 'open_question'


# ============================================================
# HTTP 工具（标准库 urllib，避免引入 requests 依赖）
# ============================================================
def _http_get(url, headers=None, timeout=ATS_TIMEOUT):
    """GET 请求，返回 (status_code, text) 或抛异常。"""
    req = request.Request(url, headers=headers or {})
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode('utf-8', errors='replace')


def _http_post_json(url, payload, headers=None, timeout=ATS_TIMEOUT):
    """POST JSON 请求，返回 (status_code, text) 或抛异常。"""
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    h = {'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    req = request.Request(url, data=body, headers=h, method='POST')
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode('utf-8', errors='replace')


def _normalize_salary(raw_salary):
    """薪资标准化：面议/空 → None，其他保留原字符串。"""
    if not raw_salary:
        return None
    s = str(raw_salary).strip()
    if s in ('面议', '', 'null', 'None'):
        return None
    return s


# ============================================================
# 北森（Beisen）适配器
# ============================================================
def _fetch_beisen(keyword, city=None, company_slug=None, page=1, page_size=20):
    """北森 ATS 公开接口。覆盖央企/国企/大厂校招。

    接口：POST m.beisen.com/Api/JobSearch/SearchV2
    鉴权：无需，需 AppId header（公开值）
    """
    url = 'https://m.beisen.com/Api/JobSearch/SearchV2'
    payload = {
        'AppId': BEISEN_APP_ID,
        'Keyword': keyword or '',
        'City': city or '',
        'PageIndex': page,
        'PageSize': page_size,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://m.beisen.com/',
    }
    try:
        status, text = _http_post_json(url, payload, headers=headers)
        data = json.loads(text)
        jobs = []
        for item in data.get('JobList', []) or data.get('jobList', []) or []:
            apply_url = item.get('Url') or item.get('url') or ''
            jobs.append(AtsJob(
                title=item.get('JobName') or item.get('jobName') or '',
                company=item.get('CompanyName') or item.get('companyName') or '',
                location=item.get('WorkPlaceName') or item.get('workPlaceName'),
                salary=_normalize_salary(item.get('SalaryStr') or item.get('salaryStr')),
                apply_url=apply_url,
                form_type=identify_form_type(apply_url),
                source_platform='beisen',
                raw=item,
            ))
        return jobs
    except (error.URLError, error.HTTPError, json.JSONDecodeError, OSError) as e:
        return {'error': f'beisen: {type(e).__name__}: {e}'}


# ============================================================
# Moka 适配器
# ============================================================
def _fetch_moka(keyword, city=None, company_slug=None, page=1, page_size=20):
    """Moka ATS 公开接口。覆盖民企大厂/外企校招。

    接口：POST app.mokahr.com/api/apply/spa/positions/search
    鉴权：无需，需 orgId（从 company_slug 或 URL 提取）
    """
    if not company_slug:
        return {'error': 'company_slug required for moka provider'}

    org_id = company_slug
    url = f'https://app.mokahr.com/api/apply/spa/positions/search?orgId={parse.quote(org_id)}'
    payload = {
        'keyword': keyword or '',
        'city': city or '',
        'page': page,
        'limit': page_size,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://app.mokahr.com/apply/{org_id}',
    }
    try:
        status, text = _http_post_json(url, payload, headers=headers)
        data = json.loads(text)
        jobs = []
        for item in data.get('data', {}).get('positions', []) or []:
            apply_url = item.get('externalUrl') or item.get('url') or ''
            jobs.append(AtsJob(
                title=item.get('title') or '',
                company=item.get('department', {}).get('name', '') if isinstance(item.get('department'), dict) else '',
                location=item.get('workLocation') or item.get('workplaceName'),
                salary=_normalize_salary(
                    f"{item.get('salaryMin','')}-{item.get('salaryMax','')}"
                    if item.get('salaryMin') else None
                ),
                apply_url=apply_url,
                form_type=identify_form_type(apply_url),
                source_platform='moka',
                raw=item,
            ))
        return jobs
    except (error.URLError, error.HTTPError, json.JSONDecodeError, OSError) as e:
        return {'error': f'moka: {type(e).__name__}: {e}'}


# ============================================================
# 牛客网适配器
# ============================================================
def _fetch_nowcoder(keyword, city=None, company_slug=None, page=1, page_size=20):
    """牛客网校招岗位搜索。

    接口：GET nowcoder.com/np/api/job/schooljobs/list
    鉴权：无需
    """
    params = {
        'keyword': keyword or '',
        'city': city or '',
        'page': page,
        'pageSize': page_size,
    }
    url = f'https://www.nowcoder.com/np/api/job/schooljobs/list?{parse.urlencode(params)}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.nowcoder.com/job/school',
    }
    try:
        status, text = _http_get(url, headers=headers)
        data = json.loads(text)
        jobs = []
        for item in data.get('data', {}).get('list', []) or []:
            apply_url = item.get('jumpUrl') or item.get('url') or ''
            jobs.append(AtsJob(
                title=item.get('title') or '',
                company=item.get('companyName') or '',
                location=item.get('city'),
                salary=_normalize_salary(item.get('salary')),
                apply_url=apply_url,
                form_type=identify_form_type(apply_url),
                source_platform='nowcoder',
                raw=item,
            ))
        return jobs
    except (error.URLError, error.HTTPError, json.JSONDecodeError, OSError) as e:
        return {'error': f'nowcoder: {type(e).__name__}: {e}'}


# ============================================================
# 应届生求职网适配器（底层走北森，或抓列表页）
# ============================================================
def _fetch_yingjiesheng(keyword, city=None, company_slug=None, page=1, page_size=20):
    """应届生求职网校招聚合。底层多走北森，复用 _fetch_beisen。

    应届生网（yingjiesheng.com）部分页面底层用北森 ATS，
    复用北森接口查询，source_platform 标记为 yingjiesheng。
    """
    result = _fetch_beisen(keyword, city=city, page=page, page_size=page_size)
    if isinstance(result, dict) and 'error' in result:
        return result
    # 覆盖 source_platform 为 yingjiesheng
    for job in result:
        job.source_platform = 'yingjiesheng'
    return result


# ============================================================
# 适配器注册表
# 按名称查找（非直接持有函数引用），便于测试 mock patch
# ============================================================
_PROVIDERS = {
    'beisen': '_fetch_beisen',
    'moka': '_fetch_moka',
    'nowcoder': '_fetch_nowcoder',
    'yingjiesheng': '_fetch_yingjiesheng',
}


def _get_provider_fn(name):
    """按名称从模块全局查找适配器函数，便于测试 mock patch。"""
    import sys
    mod = sys.modules[__name__]
    return getattr(mod, _PROVIDERS[name])


# ============================================================
# 统一入口
# ============================================================
def fetch_ats_jobs(provider='all', keyword='', city=None, company_slug=None,
                   page=1, page_size=20):
    """从国内 ATS 平台直连获取岗位列表。

    Args:
        provider: beisen | moka | nowcoder | yingjiesheng | all
        keyword: 岗位关键词
        city: 城市筛选（可空）
        company_slug: Moka 需要 orgId（可空，仅 moka 必填）
        page: 页码
        page_size: 每页数量

    Returns:
        dict: {
            jobs: [{title, company, location, salary, apply_url, form_type, source_platform, raw}],
            total: int,
            provider: str,
            errors: {platform: error_msg}  # 单家失败不阻塞
        }
    """
    if provider == 'all':
        # 并发查询全部平台
        all_jobs = []
        errors = {}
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix='ats') as ex:
            futures = {
                ex.submit(_get_provider_fn(name), keyword, city, company_slug, page, page_size): name
                for name in _PROVIDERS
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if isinstance(result, dict) and 'error' in result:
                        errors[name] = result['error']
                    else:
                        all_jobs.extend(result)
                except Exception as e:
                    errors[name] = f'{type(e).__name__}: {e}'

        # 按 (company, title) 去重
        seen = set()
        deduped = []
        for job in all_jobs:
            key = (job.company, job.title)
            if key not in seen:
                seen.add(key)
                deduped.append(job)

        return {
            'jobs': [asdict(j) for j in deduped],
            'total': len(deduped),
            'provider': 'all',
            'errors': errors,
        }

    # 单平台查询
    if provider not in _PROVIDERS:
        return {
            'jobs': [],
            'total': 0,
            'provider': provider,
            'errors': {provider: f'unknown provider: {provider}'},
        }
    fn = _get_provider_fn(provider)

    result = fn(keyword, city=city, company_slug=company_slug, page=page, page_size=page_size)
    if isinstance(result, dict) and 'error' in result:
        return {
            'jobs': [],
            'total': 0,
            'provider': provider,
            'errors': {provider: result['error']},
        }
    return {
        'jobs': [asdict(j) for j in result],
        'total': len(result),
        'provider': provider,
        'errors': {},
    }
