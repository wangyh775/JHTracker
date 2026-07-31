"""
scripts/ai_scorer.py — AI 职位匹配评分引擎

两阶段评分 + 省 token 优化：
Stage 1: 关键词预筛 (免费，零 LLM 调用)
Stage 2: LLM 批量深度评分 (一次 prompt 评 N 家，省 90%+ token)

省 token 策略：
1. 批量评分：默认 BATCH_SIZE=15，500 家从 500 次调用降到 ~34 次
2. Profile 指纹缓存：data/.profile_hash 记录上次评分时的 profile md5，
   --force 时若 profile 未变则跳过 LLM 评分（仅重跑预筛）
3. 增量评分：默认只评 score IS NULL 的公司（不重复评分）

用法：
  python scripts/ai_scorer.py                   # 给所有 score IS NULL 的公司评分
  python scripts/ai_scorer.py --force            # 重新评分（profile 未变则跳过 LLM）
  python scripts/ai_scorer.py --force --profile-changed  # 强制 LLM 重评（profile 变了）
  python scripts/ai_scorer.py --company-id 312   # 只给指定公司评分
  python scripts/ai_scorer.py --batch-size 20    # 自定义批量大小

依赖：
  pip install anthropic
  环境变量 ANTHROPIC_API_KEY 或 OPENAI_API_KEY

输出：
  直接更新数据库 companies 表的 score / score_reason 字段
"""

import os
import sys
import re
import argparse
import json
import sqlite3
import hashlib

# 把脚本所在目录（项目根目录）加入 sys.path，使 `from config import ...` 可工作
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 .env 文件（从命令行直接跑时也能读到 API Key）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 路径：统一从 config.py 读取，尊重 JH_DATA_DIR 环境变量，与 Web 应用保持同步
from config import DATA_DIR, PROFILE_FILE
DB_PATH = os.path.join(DATA_DIR, 'tracker.db')

# Profile 指纹缓存：记录上次评分时的 profile hash
PROFILE_HASH_FILE = os.path.join(DATA_DIR, '.profile_hash')

# 批量评分大小：一次 prompt 评多少家公司
DEFAULT_BATCH_SIZE = 15


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


def profile_hash(profile):
    """计算 profile 的 md5 指纹。"""
    return hashlib.md5(profile.encode('utf-8')).hexdigest()


def load_last_profile_hash():
    """读取上次评分时的 profile hash。"""
    try:
        with open(PROFILE_HASH_FILE, 'r') as f:
            return f.read().strip()
    except (OSError, IOError):
        return None


def save_profile_hash(h):
    """保存当前 profile hash。"""
    try:
        with open(PROFILE_HASH_FILE, 'w') as f:
            f.write(h)
    except OSError:
        pass


# ============ Stage 1: 关键词预筛 ============
DEAL_BREAKERS = [
    '实习', 'intern', 'internship', '管培', '保险', '销售',
    '客服', '运营', '市场', '行政', 'hr', '人力', '财务',
    '会计', '审计', '法务', '公关', '媒介', '前端', '大数据',
    '测试开发', '产品经理', '数据分析', '算法（非控制）',
    'java', 'go语言', 'web前端', 'ui设计',
]


def prefilter(job_type, match_reason, job_desc=''):
    """Stage 1: 关键词预筛。返回 (pass: bool, reason: str)。"""
    text = f"{job_type or ''} {match_reason or ''} {job_desc or ''}".lower()

    for breaker in DEAL_BREAKERS:
        if breaker.lower() in text:
            return False, f"排除词触发: {breaker}"

    return True, "预筛通过"


# ============ Stage 2: LLM 批量深度评分 ============
BATCH_SCORING_PROMPT = """你是一位专业的工科求职顾问，专门评估控制/嵌入式/机电/3D打印方向的候选人匹配度。

## 候选人简历
{profile}

## 待评估公司清单（共 {n} 家）
{companies_block}

## 评估要求
对每家公司从以下维度评估匹配度，给出 0-100 的综合评分：

1. **核心技能匹配 (40分)**：候选人的核心能力是否覆盖岗位需求
2. **行业相关度 (20分)**：公司行业方向与候选人经验的相关性
3. **职能契合度 (25分)**：岗位方向是否匹配候选人技术栈
4. **成长空间 (15分)**：候选人基础能力是否有潜力快速补上

**评分原则**：
- 90-100：完美匹配，几乎量身定制
- 70-89：高度匹配，少量差距可通过学习弥补
- 50-69：中等匹配，有较好基础但核心方向有偏差
- 30-49：低匹配，仅少数技能重合
- 0-29：不匹配，建议放弃

**重要**：行业背景差异不应大幅扣分。如果 match_reason 已是正面评价，应相应给高分。

请严格按以下 JSON 数组格式输出，不要输出其他内容：
[
  {{"id": 1, "score": 75, "reason": "匹配理由（20字内）", "missing": "缺失项（20字内，可空）"}},
  {{"id": 2, "score": 80, "reason": "...", "missing": "..."}}
]

数组长度必须等于 {n}，id 与输入一致。
"""


def _format_companies_block(companies):
    """把多家公司格式化成 prompt 文本块。"""
    lines = []
    for i, c in enumerate(companies, 1):
        lines.append(
            f"{i}. [id={c['id']}] {c['name']} | 行业:{c.get('industry') or '未知'} | "
            f"岗位:{c.get('job_type') or '未知'} | 城市:{c.get('city') or '未知'} | "
            f"优先级:{c.get('priority') or 'B'} | 匹配理由:{c.get('match_reason') or '无'} | "
            f"标签:{c.get('tags') or '无'}"
        )
    return "\n".join(lines)


def _call_llm(prompt, max_tokens=2000):
    """调用 LLM（兼容 Anthropic / OpenAI）。批量评分需要更大 max_tokens。

    失败时返回 None 并打印错误到 stderr（会被日志文件捕获）。
    """
    # 优先使用环境变量 ANTHROPIC_API_KEY
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.environ.get('AI_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=max_tokens,
                system="你是一个专业的求职匹配评估助手。请严格按 JSON 数组格式输出，不要输出其他内容。",
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except ImportError:
            print("⚠️  anthropic 库未安装，尝试 OpenAI fallback", file=sys.stderr)
        except Exception as e:
            print(f"❌ Anthropic API 调用失败: {type(e).__name__}: {e}", file=sys.stderr)
            return None

    # Fallback: OpenAI 兼容接口（9Router 用固定 dummy key，无需.env）
    api_key = 'sk-dummy'
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=os.environ.get('AI_BASE_URL', 'http://localhost:20128/v1')
            )
            print(f"DEBUG: Calling LLM with base_url={client.base_url}")
            resp = client.chat.completions.create(
                model=os.environ.get('AI_MODEL', 'Hermes'),
                max_tokens=max_tokens,
                stream=False,
                messages=[
                    {"role": "system", "content": "你是一个专业的求职匹配评估助手。请严格按 JSON 数组格式输出，不要输出其他内容。"},
                    {"role": "user", "content": prompt}
                ]
            )
            return resp.choices[0].message.content
        except ImportError:
            print("⚠️  openai 库未安装", file=sys.stderr)
        except Exception as e:
            print(f"❌ OpenAI API 调用失败: {type(e).__name__}: {e}", file=sys.stderr)
            return None

    print("⚠️  未设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY，跳过 LLM 评分", file=sys.stderr)
    return None


def _parse_batch_scores(text, expected_ids):
    """从 LLM 响应中解析 JSON 数组评分。返回 {id: (score, reason)} 字典。"""
    if not text:
        return {}
    try:
        print(f"DEBUG: LLM Response Raw: {text[:200]}")
        start = text.find('[')
        end = text.rfind(']') + 1
        if start >= 0 and end > start:
            arr = json.loads(text[start:end])
            result = {}
            for item in arr:
                cid = item.get('id')
                if cid in expected_ids:
                    score = item.get('score', 50)
                    reason = item.get('reason', '')
                    missing = item.get('missing', '')
                    full_reason = f"{reason}" + (f" | 缺: {missing}" if missing else "")
                    result[cid] = (score, full_reason)
            return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️ JSON 解析失败: {e}")
    return {}


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


def score_batch(companies, profile):
    """批量评分：一次 LLM 调用评 N 家公司。返回 {id: (score, reason)}。"""
    if not companies or not profile:
        return {}

    # 先做预筛，分离出需要 LLM 评分的
    to_llm = []
    prefiltered = {}
    for c in companies:
        passed, reason = prefilter(c.get('job_type'), c.get('match_reason'))
        if not passed:
            prefiltered[c['id']] = (0, reason)
        elif not c.get('job_type') and not c.get('match_reason'):
            prefiltered[c['id']] = (50, "基础匹配（无详细JD）")
        else:
            to_llm.append(c)

    if not to_llm:
        return prefiltered

    # 调用 LLM 批量评分
    prompt = BATCH_SCORING_PROMPT.format(
        profile=profile,
        n=len(to_llm),
        companies_block=_format_companies_block(to_llm),
    )
    response_text = _call_llm(prompt)
    expected_ids = {c['id'] for c in to_llm}
    llm_scores = _parse_batch_scores(response_text, expected_ids)

    # 合并结果：LLM 评分 + 预筛结果
    # LLM 失败的公司不给默认分，保持 None，下次增量评分会自动重试
    result = dict(prefiltered)
    for c in to_llm:
        cid = c['id']
        if cid in llm_scores:
            result[cid] = llm_scores[cid]
        else:
            # 标记为失败，但 score 保持 None（不写入 50）
            result[cid] = (None, "LLM 评分失败（JSON 漏掉或解析失败），下次重试")
    return result


PROGRESS_FILE = os.path.join(DATA_DIR, '.score_progress.json')


def write_progress(current, total, name, score, status='running'):
    """写入进度文件供前端轮询。"""
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
    parser = argparse.ArgumentParser(description='AI 职位匹配评分引擎（批量评分 + profile 指纹缓存）')
    parser.add_argument('--force', action='store_true', help='重新评分所有公司（profile 未变则跳过 LLM）')
    parser.add_argument('--profile-changed', action='store_true',
                        help='与 --force 配合：强制 LLM 重评（即使 profile 未变）')
    parser.add_argument('--company-id', type=int, help='只评分指定公司 ID')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'批量评分大小（默认 {DEFAULT_BATCH_SIZE}）')
    parser.add_argument('--dry-run', action='store_true', help='仅预览不写入')
    args = parser.parse_args()

    write_progress(0, 0, '初始化', 0, 'starting')

    # 加载候选人画像
    profile = load_candidate_profile()
    if not profile and not args.dry_run:
        print("⚠️  未配置 profile，将仅做关键词预筛，不做 LLM 深度评分。")

    # Profile 指纹缓存检查
    current_hash = profile_hash(profile) if profile else None
    last_hash = load_last_profile_hash()
    profile_unchanged = (current_hash == last_hash) if (current_hash and last_hash) else False

    skip_llm = False
    if args.force and profile_unchanged and not args.profile_changed:
        print(f"ℹ️  Profile 自上次评分以来未变化（hash={current_hash[:8]}...），跳过 LLM 评分。")
        print(f"    仅重跑关键词预筛。如需强制 LLM 重评，请加 --profile-changed。")
        skip_llm = True

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
    print(f"   批量大小: {args.batch_size} | profile 未变跳过 LLM: {skip_llm}")
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

    # 分批处理
    batch_size = max(1, args.batch_size)
    for batch_start in range(0, total, batch_size):
        batch = companies[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"\n🔄 批次 {batch_num}/{total_batches}（{len(batch)} 家）")

        if skip_llm or not profile:
            # 仅预筛，不调 LLM
            batch_scores = {}
            for c in batch:
                passed, reason = prefilter(c.get('job_type'), c.get('match_reason'))
                if passed:
                    batch_scores[c['id']] = (50, "Profile 未变/未配置，保留预筛结果")
                else:
                    batch_scores[c['id']] = (0, reason)
        else:
            # 批量 LLM 评分
            batch_scores = score_batch(batch, profile)

        # 写入数据库
        cursor = conn.cursor()
        for i, c in enumerate(batch):
            cid = c['id']
            if cid in batch_scores:
                score, reason = batch_scores[cid]
            else:
                score, reason = None, "评分缺失，下次重试"
                errors += 1

            if score is None:
                # LLM 失败：只写 reason，不写 score（保持 NULL，下次增量评分自动重试）
                cursor.execute("UPDATE companies SET score_reason = ? WHERE id = ?",
                               (reason, cid))
                conn.commit()
                global_idx = batch_start + i + 1
                write_progress(global_idx, total, c['name'], 0)
                print(f"({global_idx}/{total})  [LLM 失败] {c['name']:50s} -> {reason}")
                errors += 1
                continue

            if score == 0:
                prefiltered += 1

            cursor.execute("UPDATE companies SET score = ?, score_reason = ? WHERE id = ?",
                           (score, reason, cid))
            conn.commit()

            global_idx = batch_start + i + 1
            write_progress(global_idx, total, c['name'], score)
            msg = f"  {'[预筛淘汰]' if score == 0 else f'[评分 {score}]'} {c['name']}"
            print(f"({global_idx}/{total}) {msg:50s} -> {reason}")
            scored += 1

    # 评分完成后保存 profile hash（仅当实际调用了 LLM 且全部成功）
    if not skip_llm and profile:
        save_profile_hash(current_hash)
        print(f"\n💾 已保存 profile 指纹: {current_hash[:8]}...")

    write_progress(total, total, '完成', 0, 'done')
    print(f"\n✅ 完成！评分 {scored} 家，预筛淘汰 {prefiltered} 家，错误 {errors} 家")
    conn.close()


if __name__ == '__main__':
    main()
