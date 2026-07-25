"""笔记路由。"""
from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db
from models import Note
from utils import try_int

bp = Blueprint('note', __name__)


@bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        n = Note(
            company_id=try_int(request.form.get('company_id')) or None,
            category=request.form.get('category', 'other'),
            title=request.form['title'],
            content=request.form.get('content', ''),
        )
        db.session.add(n)
        db.session.commit()
        return redirect(url_for('note.notes'))
    page = request.args.get('page', 1, type=int)
    ns = Note.query.order_by(Note.created_at.desc()).paginate(page=page, per_page=30)
    return render_template('notes.html', notes=ns)


@bp.route('/notes/<int:n_id>/delete', methods=['POST'])
def note_delete(n_id):
    n = Note.query.get_or_404(n_id)
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for('note.notes'))
