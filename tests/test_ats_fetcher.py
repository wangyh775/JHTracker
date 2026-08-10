"""ats_fetcher.py 的单元测试。

mock 各 ATS 接口响应，验证字段映射、form_type 识别、并发去重、容错。
"""
import json
from unittest.mock import patch

import pytest

from services.sourcing.ats_fetcher import (
    AtsJob,
    fetch_ats_jobs,
    identify_form_type,
    _normalize_salary,
    _fetch_beisen,
    _fetch_moka,
    _fetch_nowcoder,
    _fetch_yingjiesheng,
)


# ============================================================
# form_type 识别
# ============================================================
class TestIdentifyFormType:
    def test_beisen_is_structured(self):
        assert identify_form_type('https://xyz.beisen.com/jobs/123') == 'structured'

    def test_yingjiesheng_is_structured(self):
        assert identify_form_type('https://www.yingjiesheng.com/job-123') == 'structured'

    def test_moka_is_structured(self):
        assert identify_form_type('https://app.mokahr.com/apply/acme/job/1') == 'structured'

    def test_nowcoder_is_structured(self):
        assert identify_form_type('https://www.nowcoder.com/jobs/123') == 'structured'

    def test_workday_is_attachment(self):
        assert identify_form_type('https://acme.wd1.myworkdayjobs.com/careers') == 'attachment'

    def test_greenhouse_is_attachment(self):
        assert identify_form_type('https://boards.greenhouse.io/acme') == 'attachment'

    def test_lever_is_attachment(self):
        assert identify_form_type('https://jobs.lever.co/acme') == 'attachment'

    def test_zhipin_is_one_click(self):
        assert identify_form_type('https://www.zhipin.com/job_detail/abc.html') == 'one_click'

    def test_unknown_defaults_to_open_question(self):
        assert identify_form_type('https://some-unknown-site.com/job') == 'open_question'

    def test_empty_url_defaults_to_open_question(self):
        assert identify_form_type('') == 'open_question'
        assert identify_form_type(None) == 'open_question'


# ============================================================
# salary 标准化
# ============================================================
class TestNormalizeSalary:
    def test_normal_string_preserved(self):
        assert _normalize_salary('15-30K·14薪') == '15-30K·14薪'

    def test_mianyi_returns_none(self):
        assert _normalize_salary('面议') is None

    def test_empty_returns_none(self):
        assert _normalize_salary('') is None
        assert _normalize_salary(None) is None

    def test_none_string_returns_none(self):
        assert _normalize_salary(None) is None


# ============================================================
# 北森适配器
# ============================================================
class TestFetchBeisen:
    @patch('services.sourcing.ats_fetcher._http_post_json')
    def test_field_mapping(self, mock_post):
        mock_post.return_value = (200, json.dumps({
            'JobList': [{
                'JobName': '嵌入式工程师',
                'CompanyName': '某央企',
                'WorkPlaceName': '北京',
                'SalaryStr': '15-25K',
                'Url': 'https://xyz.beisen.com/jobs/100',
            }]
        }))
        jobs = _fetch_beisen(keyword='嵌入式', city='北京')
        assert len(jobs) == 1
        assert isinstance(jobs[0], AtsJob)
        assert jobs[0].title == '嵌入式工程师'
        assert jobs[0].company == '某央企'
        assert jobs[0].location == '北京'
        assert jobs[0].salary == '15-25K'
        assert jobs[0].apply_url == 'https://xyz.beisen.com/jobs/100'
        assert jobs[0].source_platform == 'beisen'
        assert jobs[0].form_type == 'structured'

    @patch('services.sourcing.ats_fetcher._http_post_json')
    def test_mianyi_salary_normalized_to_none(self, mock_post):
        mock_post.return_value = (200, json.dumps({
            'JobList': [{
                'JobName': '岗位A', 'CompanyName': '公司A',
                'SalaryStr': '面议', 'Url': 'https://x.beisen.com/1',
            }]
        }))
        jobs = _fetch_beisen(keyword='A')
        assert jobs[0].salary is None

    @patch('services.sourcing.ats_fetcher._http_post_json')
    def test_network_error_returns_error_dict(self, mock_post):
        from urllib import error as url_error
        mock_post.side_effect = url_error.URLError('timeout')
        result = _fetch_beisen(keyword='A')
        assert isinstance(result, dict)
        assert 'error' in result
        assert 'beisen' in result['error']

    @patch('services.sourcing.ats_fetcher._http_post_json')
    def test_empty_joblist(self, mock_post):
        mock_post.return_value = (200, json.dumps({'JobList': []}))
        jobs = _fetch_beisen(keyword='A')
        assert jobs == []


# ============================================================
# Moka 适配器
# ============================================================
class TestFetchMoka:
    @patch('services.sourcing.ats_fetcher._http_post_json')
    def test_field_mapping(self, mock_post):
        mock_post.return_value = (200, json.dumps({
            'data': {
                'positions': [{
                    'title': '算法工程师',
                    'department': {'name': 'AI Lab'},
                    'workLocation': '深圳',
                    'salaryMin': 20,
                    'salaryMax': 40,
                    'externalUrl': 'https://app.mokahr.com/apply/acme/job/1',
                }]
            }
        }))
        jobs = _fetch_moka(keyword='算法', company_slug='acme')
        assert len(jobs) == 1
        assert jobs[0].title == '算法工程师'
        assert jobs[0].company == 'AI Lab'
        assert jobs[0].location == '深圳'
        assert '20-40' in jobs[0].salary
        assert jobs[0].source_platform == 'moka'
        assert jobs[0].form_type == 'structured'

    def test_missing_company_slug_returns_error(self):
        result = _fetch_moka(keyword='A')
        assert isinstance(result, dict)
        assert 'error' in result
        assert 'company_slug' in result['error']


# ============================================================
# 牛客网适配器
# ============================================================
class TestFetchNowcoder:
    @patch('services.sourcing.ats_fetcher._http_get')
    def test_field_mapping(self, mock_get):
        mock_get.return_value = (200, json.dumps({
            'data': {
                'list': [{
                    'title': '校招岗位',
                    'companyName': '某公司',
                    'city': '杭州',
                    'salary': '20-30K',
                    'jumpUrl': 'https://www.nowcoder.com/jobs/1',
                }]
            }
        }))
        jobs = _fetch_nowcoder(keyword='校招')
        assert len(jobs) == 1
        assert jobs[0].title == '校招岗位'
        assert jobs[0].company == '某公司'
        assert jobs[0].location == '杭州'
        assert jobs[0].salary == '20-30K'
        assert jobs[0].source_platform == 'nowcoder'
        assert jobs[0].form_type == 'structured'


# ============================================================
# 应届生适配器（复用北森）
# ============================================================
class TestFetchYingjiesheng:
    @patch('services.sourcing.ats_fetcher._fetch_beisen')
    def test_reuses_beisen_and_overrides_platform(self, mock_beisen):
        mock_beisen.return_value = [
            AtsJob(title='A', company='C', apply_url='https://x.yingjiesheng.com/1',
                   source_platform='beisen', form_type='structured')
        ]
        jobs = _fetch_yingjiesheng(keyword='A')
        assert len(jobs) == 1
        assert jobs[0].source_platform == 'yingjiesheng'

    @patch('services.sourcing.ats_fetcher._fetch_beisen')
    def test_propagates_beisen_error(self, mock_beisen):
        mock_beisen.return_value = {'error': 'beisen: timeout'}
        result = _fetch_yingjiesheng(keyword='A')
        assert isinstance(result, dict)
        assert 'error' in result


# ============================================================
# 统一入口 fetch_ats_jobs
# ============================================================
class TestFetchAtsJobs:
    @patch('services.sourcing.ats_fetcher._fetch_beisen')
    def test_single_provider(self, mock_beisen):
        mock_beisen.return_value = [
            AtsJob(title='A', company='C1', apply_url='https://x.beisen.com/1',
                   source_platform='beisen', form_type='structured'),
            AtsJob(title='B', company='C2', apply_url='https://x.beisen.com/2',
                   source_platform='beisen', form_type='structured'),
        ]
        result = fetch_ats_jobs(provider='beisen', keyword='嵌入式')
        assert result['provider'] == 'beisen'
        assert result['total'] == 2
        assert len(result['jobs']) == 2
        assert result['errors'] == {}
        # 返回的是 dict（序列化后），不是 AtsJob
        assert result['jobs'][0]['title'] == 'A'
        assert result['jobs'][0]['form_type'] == 'structured'

    @patch('services.sourcing.ats_fetcher._fetch_beisen')
    @patch('services.sourcing.ats_fetcher._fetch_moka')
    @patch('services.sourcing.ats_fetcher._fetch_nowcoder')
    @patch('services.sourcing.ats_fetcher._fetch_yingjiesheng')
    def test_all_provider_concurrent_dedup(self, mock_yjs, mock_nc, mock_moka, mock_beisen):
        # 两个平台返回同一条 (company, title)，应去重
        mock_beisen.return_value = [
            AtsJob(title='嵌入式', company='某公司', apply_url='https://x.beisen.com/1',
                   source_platform='beisen', form_type='structured'),
        ]
        mock_moka.return_value = [
            AtsJob(title='嵌入式', company='某公司', apply_url='https://app.mokahr.com/1',
                   source_platform='moka', form_type='structured'),
            AtsJob(title='算法', company='某公司', apply_url='https://app.mokahr.com/2',
                   source_platform='moka', form_type='structured'),
        ]
        mock_nc.return_value = []
        mock_yjs.return_value = []

        result = fetch_ats_jobs(provider='all', keyword='嵌入式')
        assert result['provider'] == 'all'
        # 去重后应为 2 条（嵌入式 ×1 + 算法 ×1）
        assert result['total'] == 2
        titles = [j['title'] for j in result['jobs']]
        assert '嵌入式' in titles
        assert '算法' in titles

    @patch('services.sourcing.ats_fetcher._fetch_beisen')
    @patch('services.sourcing.ats_fetcher._fetch_moka')
    def test_single_failure_does_not_block_others(self, mock_moka, mock_beisen):
        from urllib import error as url_error
        mock_beisen.side_effect = url_error.URLError('timeout')
        mock_moka.return_value = [
            AtsJob(title='A', company='C', source_platform='moka', form_type='structured'),
        ]
        result = fetch_ats_jobs(provider='all', keyword='A')
        # beisen 失败，但 moka 成功，应返回 1 条
        assert result['total'] == 1
        assert 'beisen' in result['errors']
        assert result['jobs'][0]['source_platform'] == 'moka'

    def test_unknown_provider_returns_error(self):
        result = fetch_ats_jobs(provider='unknown', keyword='A')
        assert result['total'] == 0
        assert 'unknown' in result['errors']['unknown']

    @patch('services.sourcing.ats_fetcher._fetch_moka')
    def test_moka_missing_slug_in_all_mode(self, mock_moka):
        # moka 缺 company_slug 应返回 error dict，但不阻塞其他平台
        mock_moka.return_value = {'error': 'company_slug required for moka provider'}
        with patch('services.sourcing.ats_fetcher._fetch_beisen', return_value=[
            AtsJob(title='A', company='C', source_platform='beisen', form_type='structured'),
        ]), patch('services.sourcing.ats_fetcher._fetch_nowcoder', return_value=[]), \
             patch('services.sourcing.ats_fetcher._fetch_yingjiesheng', return_value=[]):
            result = fetch_ats_jobs(provider='all', keyword='A')
            assert result['total'] == 1
            assert 'moka' in result['errors']
            assert 'company_slug' in result['errors']['moka']
