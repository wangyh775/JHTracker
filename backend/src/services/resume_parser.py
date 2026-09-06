import os
import io
import re
from typing import List, Tuple

def extract_text_from_file(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.txt', '.md', '.markdown']:
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('gbk', errors='ignore')
    elif ext == '.pdf':
        text_parts = []
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        except Exception:
            pass
        if not text_parts:
            # Fallback printable ascii and simple decode
            return content.decode('utf-8', errors='ignore')
        return '\n'.join(text_parts)
    elif ext in ['.docx', '.doc']:
        text_parts = []
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
        except Exception:
            pass
        if not text_parts:
            return content.decode('utf-8', errors='ignore')
        return '\n'.join(text_parts)
    else:
        return content.decode('utf-8', errors='ignore')

COMMON_SKILLS = [
    # 软件与编程
    'Python', 'Java', 'C++', 'C', 'Go', 'Rust', 'TypeScript', 'JavaScript',
    'React', 'Vue', 'FastAPI', 'Spring Boot', 'Django', 'Flask',
    'Docker', 'Kubernetes', 'Linux', 'Git', 'MySQL', 'PostgreSQL',
    'Redis', 'MongoDB', 'SQLite', 'Kafka', 'RabbitMQ', 'PyTorch',
    'TensorFlow', 'Pandas', 'NumPy', 'Tailwind CSS', 'Vite',
    # 机械与制造工程
    'SolidWorks', 'AutoCAD', 'CATIA', 'Creo', 'UG', 'NX', 'Pro/E',
    'ANSYS', 'Fluent', 'Abaqus', 'COMSOL', 'HyperMesh', 'Adams',
    'CFD', 'CAE', 'CAD', 'CAM', '有限元', '热流耦合', '热仿真', '结构仿真',
    '增材制造', '3D打印', 'FDM', 'SLA', 'SLM', '拓扑优化', '轻量化', '公差配合',
    # 电气与嵌入式
    'EPLAN', 'Altium Designer', 'Cadence', 'PADS', 'PLC',
    'STM32', 'ARM', 'FPGA', 'DSP', '单片机', '嵌入式', '电机驱动', '伺服控制',
    'PID', 'MPC', 'ROS', '自动控制', '机电一体化', '传感器'
]

def extract_skills_from_text(text: str) -> List[str]:
    skills = []
    text_lower = text.lower()
    for skill in COMMON_SKILLS:
        # 对中文/特殊字符用简单包含，英文字符用词边界或包含
        if re.search(r'[\u4e00-\u9fa5]', skill):
            if skill in text:
                skills.append(skill)
        else:
            pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
            if re.search(pattern, text_lower):
                skills.append(skill)
    return skills

def parse_resume_content(filename: str, content: bytes) -> Tuple[str, str, List[str]]:
    raw_text = extract_text_from_file(filename, content)
    base_name = os.path.splitext(filename)[0]
    title = base_name if base_name else '我的简历'
    for line in raw_text.splitlines():
        line_s = line.strip().replace('#', '').strip()
        if line_s and len(line_s) <= 20 and not any(k in line_s for k in ['姓名', '电话', '邮箱', 'http']):
            title = line_s
            break
    
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.md', '.markdown']:
        content_md = raw_text
    else:
        lines = [f'# {title}', '', '## 个人简历内容', '']
        paragraphs = [p.strip() for p in raw_text.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in raw_text.splitlines() if p.strip()]
        lines.extend(paragraphs)
        content_md = '\n\n'.join(lines)
        
    skills = extract_skills_from_text(raw_text)
    return title, content_md, skills
