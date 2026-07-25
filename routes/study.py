"""复习资料路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import StudyMaterial

bp = Blueprint('study', __name__)


@bp.route('/study')
def study_list():
    cat = request.args.get('category', '')
    query = StudyMaterial.query
    if cat:
        query = query.filter_by(category=cat)
    mats = query.order_by(StudyMaterial.category, StudyMaterial.title).all()
    return render_template('study.html', materials=mats)


@bp.route('/study/<int:m_id>/content')
def study_content(m_id):
    m = StudyMaterial.query.get_or_404(m_id)
    try:
        with open(m.source_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        content = f"无法读取文件 {m.source_file}: {str(e)}"
    return render_template('study_content.html', material=m, content=content)


@bp.route('/study/<int:m_id>/toggle', methods=['POST'])
def study_toggle(m_id):
    m = StudyMaterial.query.get_or_404(m_id)
    m.is_learned = not m.is_learned
    db.session.commit()
    return redirect(url_for('study.study_list'))
