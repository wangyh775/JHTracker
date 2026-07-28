"""个人画像路由。

前端只提供预览和手动编辑。AI 自动解析简历由智能体调用
skills/career-tracker-profile/SKILL.md 完成，不走 Web 路由。
"""
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
from config import DATA_DIR

bp = Blueprint('profile', __name__)
PROFILE_FILE = os.path.join(DATA_DIR, 'profile.md')

DEFAULT_PROFILE = """## 教育背景
- (学历 / 学校 / 专业 / 时间)

## 核心技术栈
- (分类列出你的技能，每行一条)

## 项目经验
1. (项目名：简述你的角色和成果)

## 目标岗位
- (你想投递的岗位方向)

## 求职偏好
- (行业 / 城市 / 企业性质偏好)
"""


@bp.route('/profile', methods=['GET'])
def profile_view():
    content = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    if not content.strip():
        content = DEFAULT_PROFILE
    return render_template('profile.html', content=content)


@bp.route('/profile/save', methods=['POST'])
def profile_save():
    content = request.form.get('content', '')
    with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    flash('✅ 个人画像已保存', 'success')
    return redirect(url_for('profile.profile_view'))
