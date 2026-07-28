"""
scripts/ai_scorer.py — AI 职位匹配评分引擎

移植自 BossHunter 的两阶段评分思路：
Stage 1: 关键词预筛 (免费，零 LLM 调用)
Stage 2: LLM 深度评分 (用候选人的简历 + JD 综合打分)

用法：
  python scripts/ai_scorer.py                   # 给所有 score IS NULL 的公司评分
  python scripts/ai_scorer.py --force            # 重新评分所有公司
  python scripts/ai_scorer.py --company-id 312   # 只给指定公司评分

依赖：
  pip install anthropic
  环境变量 ANTHROPIC_API_KEY 或在 config 中配置

输出：
  直接更新数据库 companies 表的 score / score_reason 字段
"""

import os
import sys
import re
import argparse
import json
import sqlite3

# 连接到 tracker.db
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'tracker.db')

# 候选人画像文件（用户填写，不进 git）
PROFILE_FILE = os.path.join(BASE_DIR, 'data', 'profile.md')


def load_candidate_profile():
    """从 data/profile.md 读取候选人画像。文件不存在时给出创建引导。"""
    if not os.path.exists(PROFILE_FILE):
        print(f"⚠️  未找到候选人画像文件：{PROFILE_FILE}")
        print("   请按以下结构创建该文件，再运行 AI 评分：")
        print("   ## 教育背景 / 核心技术栈 / 项目经验 / 目标岗位 / 求职偏好")
        print("   示例见 prompts/profile.example.md")
        return ""
    with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
        return f.read().strip()

# ============ Stage 1: 关键词预筛 ============
DEAL_BREAKERS = [
    '实习', 'intern', 'internship', '管培', '保险', '销售',
    '客服', '运营', '市场', '行政', 'hr', '人力', '财务',
    '会计', '审计', '法务', '公关', '媒介', '前端', '大数据',
    '测试开发', '产品经理', '数据分析', '算法（非控制）',
    'java', 'go语言', 'web前端', 'ui设计',
]

SALARY_MIN_K = 8  # 最低月薪 8k


def prefilter(job_type, match_reason, job_desc):
    """Stage 1: 关键词预筛。返回 (pass: bool, reason: str)。"""
    text = f"{job_type or ''} {match_reason or ''} {job_desc or ''}".lower()

    for breaker in DEAL_BREAKERS:
        if breaker.lower() in text:
            return False, f"排除词触发: {breaker}"

    return True, "预筛通过"


# ============ Stage 2: LLM 深度评分 ============
SCORING_PROMPT = """你是一位专业的工科求职顾问，专门评估控制/嵌入式/机电方向的候选人匹配度。

## 候选人简历
{profile}

## 目标岗位信息
- 公司：{company}
- 行业：{industry}
- 岗位方向：{job_type}
- 城市：{city}
- 优先级：{priority}
- 匹配理由原文：{match_reason}
- 备注/标签：{tags}

## 评估要求
请从以下维度评估匹配度，给出 0-100 的综合评分：

1. **核心技能匹配 (40分)**：候选人的核心能力（运动控制/Klipper/嵌入式/MCU/PID/电机控制）是否覆盖岗位需求
2. **行业相关度 (20分)**：该公司的行业方向（机器人/3D打印/自动化/航天/军工）与候选人经验的相关性
3. **职能契合度 (25分)**：岗位方向（控制算法/嵌入式/机电/硬件）是否匹配候选人的技术栈
4. **成长空间 (15分)**：虽然可能有部分技能不匹配，但候选人的基础能力是否有潜力快速补上

**评分原则**：
- 90-100：完美匹配，几乎量身定制
- 70-89：高度匹配，少量差距可通过学习弥补
- 50-69：中等匹配，有较好的基础但核心方向有偏差
- 30-49：低匹配，仅少数技能重合
- 0-29：不匹配，建议放弃

**重要**：行业背景差异不应大幅扣分。如果岗位在航天/军工领域但候选人有机电控制背景，应视为基础能力匹配。
如果 match_reason 已经是正面评价(如"运动控制/PID/嵌入式高度相关")，应相应给高分。

请严格按以下 JSON 格式输出，不要输出其他内容：
{{"score": 75, "reason": "匹配理由（20字内）", "missing": "缺失项（20字内）"}}
"""


def _call_llm(prompt, max_tokens=300):
    """调用 LLM 进行评分（兼容 Anthropic API / OpenAI）。"""
    # 优先使用环境变量 ANTHROPIC_API_KEY
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system="你是一个专业的求职匹配评估助手。请严格按 JSON 格式输出。",
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except ImportError:
            pass

    # Fallback: OpenAI 兼容接口
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
            )
            resp = client.chat.completions.create(
                model="kr/claude-sonnet-4",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": "你是一个专业的求职匹配评估助手。请严格按 JSON 格式输出。"},
                    {"role": "user", "content": prompt}
                ]
            )
            return resp.choices[0].message.content
        except ImportError:
            pass

    print("⚠️  未设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY，跳过 LLM 评分")
    return None


def _parse_score(text):
    """从 LLM 响应中提取 JSON 评分。"""
    if not text:
        return None
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return None


# ============ 主流程 ============
def get_pending_companies(conn, force=False, company_id=None):
    """获取待评分的公司列表。"""
    c = conn.cursor()
    if company_id:
        c.execute("SELECT id, name, industry, job_type, city, priority, match_reason, tags, score "
                  "FROM companies WHERE id = ?", (company_id,))
    elif force:
        c.execute("SELECT id, name, industry, job_type, city, priority, match_reason, tags, score "
                  "FROM companies")
    else:
        c.execute("SELECT id, name, industry, job_type, city, priority, match_reason, tags, score "
                  "FROM companies WHERE score IS NULL")
    rows = c.fetchall()
    columns = ['id', 'name', 'industry', 'job_type', 'city', 'priority', 'match_reason', 'tags', 'score']
    return [dict(zip(columns, r)) for r in rows]


def score_company(company, profile):
    """对单个公司执行两阶段评分。profile 为候选人画像文本。"""
    # Stage 1: 预筛
    passed, reason = prefilter(
        company.get('job_type'),
        company.get('match_reason'),
        ''
    )
    if not passed:
        return 0, reason

    # Stage 2: LLM 深度评分
    if not company.get('job_type') and not company.get('match_reason'):
        # 没有岗位信息，给默认分
        return 50, "基础匹配（无详细JD）"

    if not profile:
        return 50, "未配置候选人画像，使用基础评分"

    prompt = SCORING_PROMPT.format(
        profile=profile,
        company=company['name'],
        industry=company.get('industry') or '未知',
        job_type=company.get('job_type') or '未知',
        city=company.get('city') or '未知',
        priority=company.get('priority') or 'B',
        match_reason=company.get('match_reason') or '无',
        tags=company.get('tags') or '无',
    )

    response_text = _call_llm(prompt)
    result = _parse_score(response_text)

    if result:
        score = result.get('score', 50)
        reason = result.get('reason', '')
        missing = result.get('missing', '')
        full_reason = f"{reason}" + (f" | 缺: {missing}" if missing else "")
        return score, full_reason
    else:
        return 50, "LLM 评分失败，默认中分"


PROGRESS_FILE = os.path.join(BASE_DIR, 'data', '.score_progress.json')


def write_progress(current, total, name, score, status='running'):
    """写入进度文件供前端轮询。"""
    import json
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                'current': current,
                'total': total,
                'name': name,
                'score': score,
                'status': status,
            }, f)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description='AI 职位匹配评分引擎')
    parser.add_argument('--force', action='store_true', help='重新评分所有公司')
    parser.add_argument('--company-id', type=int, help='只评分指定公司 ID')
    parser.add_argument('--dry-run', action='store_true', help='仅预览不写入')
    args = parser.parse_args()

    write_progress(0, 0, '初始化', 0, 'starting')

    # 加载候选人画像
    profile = load_candidate_profile()
    if not profile and not args.dry_run:
        print("⚠️  未配置 profile，将仅做关键词预筛，不做 LLM 深度评分。")

    conn = sqlite3.connect(DB_PATH)
    companies = get_pending_companies(conn, force=args.force, company_id=args.company_id)

    if not companies:
        write_progress(0, 0, '无需评分（已有评分）', 0, 'done')
        print("✅ 没有待评分的公司（所有公司已有评分）。使用 --force 重新评分。")
        conn.close()
        return

    total = len(companies)
    write_progress(0, total, '开始评分', 0, 'running')

    print(f"📊 待评分公司: {total} 家")
    if args.dry_run:
        write_progress(0, 0, 'Dry-run 模式', 0, 'done')
        print("🔍 Dry-run 模式，仅预览")
        for c in companies:
            print(f"  [{c['id']}] {c['name']} | {c.get('job_type') or '-'} | {c.get('match_reason', '')[:40]}")
        conn.close()
        return

    scored = 0
    prefiltered = 0
    errors = 0

    for i, c in enumerate(companies):
        score, reason = score_company(c, profile)
        if score == 0:
            prefiltered += 1

        write_progress(i + 1, total, c['name'], score)

        msg = f"  {'[预筛淘汰]' if score == 0 else f'[评分 {score}]'} {c['name']}"
        print(f"({i+1}/{total}) {msg:50s} -> {reason}")

        cursor = conn.cursor()
        cursor.execute("UPDATE companies SET score = ?, score_reason = ? WHERE id = ?",
                       (score, reason, c['id']))
        conn.commit()

        if score >= 0:
            scored += 1

    write_progress(total, total, '完成', 0, 'done')
    print(f"\n✅ 完成！评分 {scored} 家，预筛淘汰 {prefiltered} 家")
    conn.close()


if __name__ == '__main__':
    main()
