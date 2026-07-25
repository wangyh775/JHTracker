"""数据导入路由：公司、复习资料、时间线。"""
import os
import glob
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Company, StudyMaterial, Timeline
from config import Config
from constants import infer_priority, infer_industry_from_filename
from utils import parse_markdown_table, parse_date

bp = Blueprint('import_data', __name__)


@bp.route('/import')
def import_page():
    return render_template('import.html')


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
            headers, rows = parse_markdown_table(lines)
            if not headers:
                failed_rows.append(f'{os.path.basename(fp)}: 未找到表格')
                continue

            # 找出列名对应的 header
            name_key = _find_header(headers, ['公司', '公司名称', '名称'])
            city_key = _find_header(headers, ['城市', '地点'])
            job_key = _find_header(headers, ['岗位', '职位', '方向'])
            reason_key = _find_header(headers, ['匹配', '理由', '匹配理由'])

            if not name_key:
                failed_rows.append(f'{os.path.basename(fp)}: 找不到公司名列')
                continue

            industry = infer_industry_from_filename(fp)

            for row in rows:
                name = row.get(name_key, '').replace('**', '').strip()
                if not name:
                    continue
                existing = Company.query.filter_by(name=name).first()
                if existing:
                    skipped_count += 1
                    continue
                priority = infer_priority(name)
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
            db.session.commit()
        except Exception as e:
            failed_rows.append(f'{os.path.basename(fp)}: {str(e)}')

    if failed_rows:
        flash(f'导入完成。新增 {imported_count} 家，跳过 {skipped_count} 家。失败：{"; ".join(failed_rows)}')
    else:
        flash(f'导入完成。新增 {imported_count} 家，跳过 {skipped_count} 家。')
    return redirect(url_for('company.company_list'))


def _find_header(headers, candidates):
    """从 headers 中找第一个匹配 candidates 的列名。"""
    for h in headers:
        for c in candidates:
            if c in h:
                return h
    return None


@bp.route('/import/study', methods=['POST'])
def import_study():
    """从面试复习手册导入科目分类。"""
    path = os.path.join(Config.CAREER_DIR, Config.STUDY_FILE)
    cats = {
        '自动控制原理': 'control', '机械设计基础': 'mechanical', '传感器与检测技术': 'sensor',
        '电机与运动控制': 'motor', '嵌入式与编程': 'embedded', 'PLC与工业网络': 'plc',
        '热工基础': 'thermal', '面试行为问题': 'behavior'
    }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            f.read()  # 仅验证可读
        for cn, cat in cats.items():
            existing = StudyMaterial.query.filter_by(category=cat).first()
            if not existing:
                sm = StudyMaterial(title=f"面试复习——{cn}", category=cat,
                                   source_file=path, summary=f"自动导入：{cn}", is_learned=False)
                db.session.add(sm)
        db.session.commit()
        flash('复习资料导入完成')
    except Exception as e:
        flash(f'复习资料导入失败：{str(e)}')

    path2 = os.path.join(Config.CAREER_DIR, Config.CODING_FILE)
    try:
        with open(path2, 'r', encoding='utf-8') as f:
            f.read()
        existing = StudyMaterial.query.filter_by(category='coding').first()
        if not existing:
            sm = StudyMaterial(title="面试编程题集（12题）", category='coding',
                               source_file=path2, summary="自动导入：PID仿真、串口通信、运动控制等", is_learned=False)
            db.session.add(sm)
            db.session.commit()
        flash('编程题集导入完成')
    except Exception as e:
        flash(f'编程题集导入失败：{str(e)}')

    return redirect(url_for('study.study_list'))


@bp.route('/import/timeline', methods=['POST'])
def import_timeline():
    """添加秋招关键节点。"""
    nodes = [
        ('2026-07-25', '2026-07-25', '秋招正式启动', '开始大规模投递，完成简历优化', 'action'),
        ('2026-08-15', '2026-08-15', '拓竹提前批截止', '确认投递状态', 'deadline'),
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
