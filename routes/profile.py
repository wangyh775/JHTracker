"""个人画像路由。"""
import os
import json
import tempfile
from flask import Blueprint, render_template, request, flash, redirect, url_for
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
- 硕士在读，机械工程 (2024-2027)

## 核心技术栈
- 控制系统：Klipper 固件二次开发, MPC/PID控制
- 嵌入式：ARM Cortex-M 系列 MCU
- 软件：Python, C, C++

## 目标岗位
- 控制算法工程师 (运动控制/电机控制)
- 嵌入式软件/硬件工程师
"""
    return render_template('profile.html', content=content)


@bp.route('/profile/save', methods=['POST'])
def profile_save():
    content = request.form.get('content', '')
    with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    flash('✅ 个人画像已保存', 'success')
    return redirect(url_for('profile.profile_view'))


@bp.route('/profile/upload', methods=['POST'])
def profile_upload():
    """上传简历并调用 LLM 解析为结构化画像。"""
    from dotenv import load_dotenv
    load_dotenv()

    file = request.files.get('resume')
    if not file or not file.filename:
        flash('❌ 请选择简历文件', 'danger')
        return redirect(url_for('profile.profile_view'))

    if not allowed_file(file.filename):
        flash('❌ 仅支持 PDF 或 Word 文档', 'danger')
        return redirect(url_for('profile.profile_view'))

    # 保存到临时文件
    tmp = tempfile.NamedTemporaryFile(suffix='.' + file.filename.rsplit('.', 1)[1], delete=False)
    file.save(tmp.name)
    tmp.close()

    try:
        # 先提取文本
        text = extract_resume_text(tmp.name)
        if not text or len(text.strip()) < 50:
            flash('❌ 无法提取简历文本，请确认文件内容正确', 'danger')
            os.unlink(tmp.name)
            return redirect(url_for('profile.profile_view'))

        # 用 LLM 解析为结构化画像
        parsed = parse_with_llm(text)
        if parsed:
            with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
                f.write(parsed)
            flash('✅ 简历解析成功！个人画像已更新。建议重新评分以刷新匹配度。', 'success')
        else:
            flash('⚠️ LLM 解析失败，已将原始文本保存为画像（可手动编辑）', 'warning')
            with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
                f.write(f"## 原始简历文本（待整理）\n\n{text[:3000]}")

    except Exception as e:
        flash(f'❌ 解析失败：{str(e)[:80]}', 'danger')

    os.unlink(tmp.name)
    return redirect(url_for('profile.profile_view'))


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
    """调用本地 LLM 将简历文本转为结构化画像。"""
    api_key = os.environ.get('OPENAI_API_KEY')
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
        client = OpenAI(
            api_key=api_key,
            base_url=os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        )
        resp = client.chat.completions.create(
            model="kr/claude-sonnet-4",
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
