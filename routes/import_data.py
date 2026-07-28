"""数据导入路由：公司清单、时间线初始化。AI 评分由智能体 skill 驱动，见 skills/career-tracker-scorer/。"""
import os
import glob
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from extensions import db
from models import Company, Timeline
from config import Config, DATA_DIR
from constants import infer_priority, infer_industry_from_filename
from utils import parse_all_markdown_tables, parse_date

bp = Blueprint('import_data', __name__)


@bp.route('/import')
def import_page():
    from sqlalchemy import func
    scored = db.session.query(func.count(Company.id)).filter(Company.score.isnot(None)).scalar() or 0
    total = db.session.query(func.count(Company.id)).scalar() or 0
    pending = total - scored
    return render_template('import.html',
                           scored_count=scored,
                           pending_count=pending,
                           total_count=total)


@bp.route('/import/companies', methods=['POST'])
def import_companies():
    """从 career/ 目录的 markdown 清单批量导入公司。"""
    source = request.form.get('source', 'A')
    pattern = os.path.join(Config.CAREER_DIR, Config.COMPANY_FILE_PATTERN.format(source=source))
    files = glob.glob(pattern)
    if not files:
        all_md = glob.glob(os.path.join(Config.CAREER_DIR, '*.md'))
        files = [f for f in all_md if '企业清单' in os.path.basename(f)]

    imported_count = 0
    skipped_count = 0
    failed_rows = []

    for fp in files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tables = parse_all_markdown_tables(lines)
            if not tables:
                failed_rows.append(f'{os.path.basename(fp)}: 未找到表格')
                continue

            file_industry = infer_industry_from_filename(fp)
            file_updated = False

            for headers, rows in tables:
                # 严格匹配公司名列，跳过总览统计表/薪资表/策略表
                name_key = _find_company_name_header(headers)
                if not name_key:
                    continue
                city_key = _find_header(headers, ['城市', '地点'])
                job_key = _find_header(headers, ['岗位', '职位', '方向'])
                reason_key = _find_header(headers, ['匹配', '理由', '匹配理由'])
                sub_industry_key = _find_header(headers, ['细分行业', '行业'])

                for row in rows:
                    name = row.get(name_key, '').replace('**', '').strip()
                    if not name:
                        continue
                    if name in _HEADER_NAME_KEYWORDS:
                        continue
                    existing = Company.query.filter_by(name=name).first()
                    if existing:
                        skipped_count += 1
                        continue
                    priority = infer_priority(name)
                    # 优先用行内的细分行业，其次文件名推断
                    row_industry = row.get(sub_industry_key, '').strip() if sub_industry_key else ''
                    industry = row_industry or file_industry
                    c = Company(
                        name=name,
                        industry=industry,
                        city=row.get(city_key, '').strip() if city_key else '',
                        job_type=row.get(job_key, '').strip() if job_key else '',
                        match_reason=row.get(reason_key, '').strip() if reason_key else '',
                        priority=priority,
                        source_list=f'清单{source}',
                    )
                    db.session.add(c)
                    imported_count += 1
                    file_updated = True
            if file_updated:
                db.session.commit()
        except Exception as e:
            failed_rows.append(f'{os.path.basename(fp)}: {str(e)}')

    if failed_rows:
        flash(f'导入完成。新增 {imported_count} 家，跳过 {skipped_count} 家。失败：{"; ".join(failed_rows)}')
    else:
        flash(f'导入完成。新增 {imported_count} 家，跳过 {skipped_count} 家。')
    return redirect(url_for('company.company_list'))


def _find_header(headers, candidates):
    """从 headers 中找第一个匹配 candidates 的列名（子串匹配）。"""
    for h in headers:
        for c in candidates:
            if c in h:
                return h
    return None


def _find_company_name_header(headers):
    """严格匹配公司名列：必须是 '公司名称' / '公司' / '名称' 之一（精确匹配）。
    避免把 '公司数量' / '推荐公司举例' 等误判为公司名列。
    """
    for target in ['公司名称', '公司', '名称']:
        if target in headers:
            return target
    return None


# 表头行关键字：导入时误入库的 markdown 表头，重新同步时清理
_HEADER_NAME_KEYWORDS = {'序号', '公司名称', '名称', '#', '排名', '行业', '公司数量'}


@bp.route('/import/companies/resync', methods=['POST'])
def import_companies_resync():
    """从源 markdown 重新读取，按公司名更新现有 Company 的字段（修存量数据错位）。

    - 保留：id、priority、salary_min/max、source_list、created_at、applications、notes
    - 更新：city、industry、job_type、match_reason
    - 清理：误入库的表头行
    - 多表文件：迭代每张表，跳过无公司名列的表（如总览统计表）
    - 行业：优先用源行的细分行业/行业列，回退到文件名推断
    - 防交叉污染：只从与公司 source_list 匹配的文件更新（清单A 公司不从清单B 覆盖）
    """
    all_md = glob.glob(os.path.join(Config.CAREER_DIR, '*.md'))
    files = [f for f in all_md if '企业清单' in os.path.basename(f)]
    if not files:
        flash('未找到企业清单 markdown 文件')
        return redirect(url_for('import_data.import_page'))

    updated_count = 0
    not_found_count = 0
    skipped_cross_source = 0
    failed_rows = []

    for fp in files:
        try:
            file_source = _infer_source_from_filename(fp)  # '清单A' / '清单B' / None
            with open(fp, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tables = parse_all_markdown_tables(lines)
            if not tables:
                failed_rows.append(f'{os.path.basename(fp)}: 未找到表格')
                continue

            file_industry = infer_industry_from_filename(fp)

            for headers, rows in tables:
                # 严格匹配公司名列，跳过总览统计表/薪资表/策略表
                name_key = _find_company_name_header(headers)
                if not name_key:
                    continue
                city_key = _find_header(headers, ['城市', '地点'])
                job_key = _find_header(headers, ['岗位', '职位', '方向'])
                reason_key = _find_header(headers, ['匹配', '理由', '匹配理由'])
                sub_industry_key = _find_header(headers, ['细分行业', '行业'])

                for row in rows:
                    name = row.get(name_key, '').replace('**', '').strip()
                    if not name:
                        continue
                    # 跳过表头行
                    if name in _HEADER_NAME_KEYWORDS:
                        continue
                    existing = Company.query.filter_by(name=name).first()
                    if not existing:
                        not_found_count += 1
                        continue
                    # 防交叉污染：公司 source_list 必须匹配文件来源
                    if file_source and existing.source_list and existing.source_list != file_source:
                        skipped_cross_source += 1
                        continue
                    # 更新字段（保留 id、priority、salary、关联数据）
                    existing.city = row.get(city_key, '').strip() if city_key else existing.city
                    # 行业：优先用源行的细分行业/行业列，回退到文件名推断
                    row_industry = row.get(sub_industry_key, '').strip() if sub_industry_key else ''
                    existing.industry = row_industry or file_industry
                    existing.job_type = row.get(job_key, '').strip() if job_key else existing.job_type
                    existing.match_reason = row.get(reason_key, '').strip() if reason_key else existing.match_reason
                    updated_count += 1
            db.session.commit()
        except Exception as e:
            failed_rows.append(f'{os.path.basename(fp)}: {str(e)}')

    # 清理误入库的表头行
    header_rows = Company.query.filter(Company.name.in_(_HEADER_NAME_KEYWORDS)).all()
    header_count = len(header_rows)
    for h in header_rows:
        db.session.delete(h)
    db.session.commit()

    msg = (f'重新同步完成。更新 {updated_count} 家，未匹配 {not_found_count} 家，'
           f'跨源跳过 {skipped_cross_source} 家，清理表头行 {header_count} 条。')
    if failed_rows:
        msg += f' 失败：{"; ".join(failed_rows)}'
    flash(msg)
    return redirect(url_for('import_data.import_page'))


def _infer_source_from_filename(fp):
    """从文件名推断 source_list 值：'清单A' / '清单B' / None。"""
    bn = os.path.basename(fp)
    if '_A_' in bn or '_A.' in bn:
        return '清单A'
    if '_B_' in bn or '_B.' in bn:
        return '清单B'
    return None


@bp.route('/import/timeline', methods=['POST'])
def import_timeline():
    """添加秋招关键节点。"""
    nodes = [
        ('2026-07-25', '2026-07-25', '秋招正式启动', '开始大规模投递，完成简历优化', 'action'),
        ('2026-08-15', '2026-08-15', '提前批截止', '确认目标公司提前批投递状态', 'deadline'),
        ('2026-09-01', '2026-09-30', '秋招正式批高峰', '全面铺开投递，预计每日投3-5家', 'action'),
        ('2026-09-15', '2026-10-31', '面试高发期', '大量笔试/一面', 'milestone'),
        ('2026-10-01', '2026-10-31', '大论文初稿完成', '毕业论文主体完成，腾出精力面试', 'milestone'),
        ('2026-10-31', '2026-10-31', '秋招投递截止', '大部分公司秋招网申截止', 'deadline'),
        ('2026-11-01', '2026-11-15', 'Offer决策期', '评估所有offer，做最终决定', 'milestone'),
        ('2026-12-01', '2026-12-15', '毕业论文定稿', '修改完善论文准备答辩', 'deadline'),
        ('2027-03-01', '2027-04-30', '春招启动', '如秋招未果，春招补充', 'action'),
    ]
    added = 0
    for dt_start, dt_end, title, desc, typ in nodes:
        existing = Timeline.query.filter_by(title=title).first()
        if not existing:
            t = Timeline(
                event_date=parse_date(dt_start),
                end_date=parse_date(dt_end),
                title=title, description=desc, event_type=typ
            )
            db.session.add(t)
            added += 1
    db.session.commit()
    flash(f'时间线导入完成，新增 {added} 条')
    return redirect(url_for('timeline.timeline_view'))

