import pytest
from src.services.spiders.wondercv_spider import WondercvSpider
from src.services.spiders.fangzhou_spider import sanitize_date_str, normalize_education_str
from src.services.spiders.nowcoder_spider import NowcoderSpider

def test_wondercv_enhanced_parser_rules():
    spider = WondercvSpider()
    html = """
    <div class="campus-job-card">
        <a class="company" href="/company/c1">上汽大乘用车</a>
        <a class="title" href="/xiaozhao/saic-test-123-abc/">
            上汽大乘用车2027届全球校园招聘正式启动，面向海内外2027届应届毕业生，招聘方向涵盖创新研发、智能制造、国内/国际营销...
        </a>
        <div class="info-tags">
            <span>郑州</span>
            <span>上海</span>
            <span>海外</span>
            <span>国家统招全日制本科及以上学历</span>
            <span>民营企业</span>
            <span>2027届</span>
        </div>
        <div class="category">整车集成与架构开发</div>
    </div>
    """
    jobs = spider.parse_html_page(html)
    assert len(jobs) == 1
    job = jobs[0]

    # 1. 标题精简，不超长
    assert job.title == "上汽大乘用车2027届全球校园招聘正式启动"
    # 2. 地点优先提取国内城市，不被“海外”冲刷
    assert "郑州" in job.location
    assert "上海" in job.location
    # 3. 学历规范化
    assert job.education_req == "本科"
    # 4. 企业性质归入 type_tags，行业分类保持规范
    assert "民营企业" in job.type_tags
    assert job.industry != "民营企业"

def test_fangzhou_helper_rules():
    assert normalize_education_str("国家统招全日制本科及以上学历") == "本科"
    assert normalize_education_str("硕士研究生") == "硕士"
    assert normalize_education_str("博士") == "博士"
    assert normalize_education_str("不限") == "不限"
    assert sanitize_date_str("2026-09-01") == "2026-09-01"

def test_nowcoder_deadline_handling():
    spider = NowcoderSpider()
    item = {
        "companyId": 123,
        "name": "测试云计算",
        "batchName": "2027秋招",
        "cityList": ["深圳"],
        "wangshenEndDate": None,  # 无确定截止日期
        "careerJobNameList": ["后端开发工程师"]
    }
    jobs = spider.parse_schedule_card(item)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.deadline is None
    assert "招满即止" in job.type_tags
