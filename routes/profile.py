"""个人画像路由。"""
import os
import json
import tempfile
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from config import DATA_DIR

bp = Blueprint('profile', __name__)
PROFILE_FILE = os.path.join(DATA_DIR, 'profile.md')
ALLOWED_EXT = {'pdf', 'docx'}


def allowed_file(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@bp.route('/profile', methods=['GET'])
def profile_view():
    content = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = """## 教育背景
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
    return render_template('profile.html', content=content,
                           ai_configured=bool(current_app.config.get('AI_API_KEY', '')),
                           ai_provider=current_app.config.get('AI_PROVIDER', 'anthropic'),
                           ai_model=current_app.config.get('AI_MODEL', 'gpt-4o-mini'))


@bp.route('/profile/save', methods=['POST'])
def profile_save():
    content = request.form.get('content', '')
    with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    flash('✅ 个人画像已保存', 'success')
    return redirect(url_for('profile.profile_view'))


@bp.route('/profile/upload', methods=['POST'])
def profile_upload():
    """上传简历并调用 LLM 解析为结构化画像。返回 JSON 供前端 AJAX 显示进度。"""
    from dotenv import load_dotenv
    load_dotenv()

    file = request.files.get('resume')
    if not file or not file.filename:
        return {'ok': False, 'msg': '请选择简历文件'}, 400

    if not allowed_file(file.filename):
        return {'ok': False, 'msg': '仅支持 PDF 或 Word 文档'}, 400

    # 保存到临时文件
    tmp = tempfile.NamedTemporaryFile(suffix='.' + file.filename.rsplit('.', 1)[1], delete=False)
    file.save(tmp.name)
    tmp.close()

    try:
        # 提取文本
        text = extract_resume_text(tmp.name)
        if not text or len(text.strip()) < 50:
            os.unlink(tmp.name)
            return {'ok': False, 'msg': '无法提取简历文本，请确认文件内容正确'}, 400

        # 用 LLM 解析
        parsed = parse_with_llm(text)
        if parsed:
            with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
                f.write(parsed)
            return {'ok': True, 'msg': '简历解析成功！个人画像已更新。建议重新评分以刷新匹配度。',
                    'fallback': False}
        else:
            # LLM 未配置或失败，保存原始文本
            with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
                f.write(f"## 原始简历文本（待整理）\n\n{text[:3000]}")
            return {'ok': True, 'msg': 'LLM 未配置或解析失败，已保存原始文本（可手动编辑）。',
                    'fallback': True}

    except Exception as e:
        return {'ok': False, 'msg': f'解析失败：{str(e)[:80]}'}, 500
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def extract_resume_text(filepath):
    """从 PDF/Word 提取文本。"""
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        try:
            import PyPDF2
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            pass
        try:
            import pdfminer.high_level
            text = pdfminer.high_level.extract_text(filepath)
            return text
        except ImportError:
            pass
        # fallback: pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        except ImportError:
            return None
    elif ext == 'docx':
        try:
            from docx import Document
            doc = Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return None
    return None


def parse_with_llm(text):
    """调用 LLM 将简历文本转为结构化画像。使用 app config 中的 AI 配置。"""
    api_key = current_app.config.get('AI_API_KEY', '')
    if not api_key:
        return None

    prompt = f"""你是一位求职顾问。请将以下简历文本整理为结构化的个人画像，严格按这个格式输出：

## 教育背景
- (学历/学校/专业/时间)

## 核心技术栈
- (分类技能，每行一条)

## 项目经验
1. (项目名：简述)

## 目标岗位
- (岗位方向)

## 求职偏好
- (行业/城市/性质偏好)

以下是简历原文：
{text[:4000]}
"""

    try:
        from openai import OpenAI
        base_url = current_app.config.get('AI_BASE_URL') or None
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=current_app.config.get('AI_MODEL', 'gpt-4o-mini'),
            max_tokens=2000,
            messages=[
                {"role": "system", "content": "你是一个专业的求职简历整理助手。输出结构化 Markdown。"},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[profile] LLM parse failed: {e}")
        return None
