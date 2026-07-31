"""
scripts/induce_positive_rules.py — 从历史 approve 记录批量归纳正向偏好规则

策略（方案 3 + 方案 1 补充）：
  批量归纳保证质量：把历史 approve 的 application + company 信息分批喂 LLM，
  让 LLM 提取结构化 prefer_* 规则写入 memories 表。
  显式工具允许修正：用户/Agent 可用 add_memory_rule / delete_memory_rule 手动增删。

省 token 优化（复用 ai_scorer.py 骨架）：
  1. 批量归纳：默认 BATCH_SIZE=15，一次 prompt 处理 N 条 approve
  2. 指纹缓存：data/.positive_induction_fingerprint 记录上次归纳时的
     (approve 应用列表 + profile) 指纹，无新 approve 时跳过 LLM
  3. 去重写入：按 (category, rule_value) 去重，不重复写已存在规则

用法：
  python scripts/induce_positive_rules.py                  # 归纳新 approve（指纹未变则跳过）
  python scripts/induce_positive_rules.py --force          # 强制重新归纳
  python scripts/induce_positive_rules.py --batch-size 20  # 自定义批量大小
  python scripts/induce_positive_rules.py --dry-run        # 仅预览不写库

依赖：
  pip install anthropic  (或 openai)
  环境变量 ANTHROPIC_API_KEY 或 OPENAI_API_KEY / AI_BASE_URL
"""

import os
import sys
import json
import sqlite3
import hashlib
import argparse

# 把项目根目录加入 sys.path，使 from config import ... 可工作
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import DATA_DIR, PROFILE_FILE
DB_PATH = os.path.join(DATA_DIR, 'tracker.db')

# 指纹缓存：记录上次归纳时的 (approve 列表 + profile) hash
FINGERPRINT_FILE = os.path.join(DATA_DIR, '.positive_induction_fingerprint')

DEFAULT_BATCH_SIZE = 15

# 正向规则类别（与 constants.MEMORY_CATEGORIES_POSITIVE 对齐）
POSITIVE_CATEGORIES = ['prefer_tech', 'prefer_domain', 'prefer_company', 'salary_expected', 'culture_fit']


def load_profile():
    """读取候选人画像。"""
    if not os.path.exists(PROFILE_FILE):
        return ""
    with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
        return f.read().strip()


def compute_fingerprint(approve_ids, profile):
    """计算 (approve 列表 + profile) 的 md5 指纹。"""
    raw = json.dumps(sorted(approve_ids), ensure_ascii=False) + "|" + profile
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def load_last_fingerprint():
    try:
        with open(FINGERPRINT_FILE, 'r') as f:
            return f.read().strip()
    except (OSError, IOError):
        return None


def save_fingerprint(fp):
    try:
        with open(FINGERPRINT_FILE, 'w') as f:
            f.write(fp)
    except OSError:
        pass


def get_approved_applications(conn):
    """查询所有已 approve 的 application（含 company 信息）。"""
    c = conn.cursor()
    c.row_factory = sqlite3.Row
    c.execute("""
        SELECT a.id, a.position, a.job_desc, a.channel,
               c.name AS company_name, c.industry, c.city
        FROM applications a
        LEFT JOIN companies c ON a.company_id = c.id
        WHERE a.status = 'Applied'
        ORDER BY a.id ASC
    """)
    return [dict(r) for r in c.fetchall()]


def _format_batch_block(apps):
    """把一批 approve 格式化成 prompt 文本块。"""
    lines = []
    for i, a in enumerate(apps, 1):
        jd_preview = (a.get('job_desc') or '')[:200]
        lines.append(
            f"{i}. [id={a['id']}] 公司:{a.get('company_name') or '未知'} | "
            f"行业:{a.get('industry') or '未知'} | 城市:{a.get('city') or '未知'} | "
            f"岗位:{a.get('position') or '未知'} | JD摘要:{jd_preview}"
        )
    return "\n".join(lines)


INDUCTION_PROMPT = """你是一位求职偏好分析专家。下面是候选人已 approve（认可/投递）的岗位清单。
请从中归纳出候选人的正向偏好规则，用于后续 JD 匹配加分。

## 候选人画像
{profile}

## 已 approve 岗位清单（共 {n} 条）
{apps_block}

## 归纳要求
提取以下类别的正向偏好规则：
- prefer_tech: 偏好的技术栈/技能（如 ROS、C++、Python、STM32）
- prefer_domain: 偏好的行业领域（如 机器人、3D打印、工业自动化）
- prefer_company: 偏好的公司特征（如 拓竹、大疆等具体公司名）
- salary_expected: 期望薪资下限（数字，如 15000）
- culture_fit: 文化契合偏好（如 扁平管理、技术驱动）

只提取能从 approve 记录中合理推断的规则，不要臆测。
rule_value 应为简洁的结构化值（技术名/行业名/公司名/数字），便于后续子串匹配。

请严格按以下 JSON 数组格式输出，不要输出其他内容：
[
  {{"category": "prefer_tech", "rule_value": "ROS"}},
  {{"category": "prefer_domain", "rule_value": "机器人"}}
]
"""


def _call_llm(prompt, max_tokens=2000):
    """调用 LLM（兼容 Anthropic / OpenAI）。失败返回 None。"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.environ.get('AI_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=max_tokens,
                system="你是求职偏好分析助手。请严格按 JSON 数组格式输出，不要输出其他内容。",
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except ImportError:
            print("⚠️  anthropic 库未安装，尝试 OpenAI fallback", file=sys.stderr)
        except Exception as e:
            print(f"❌ Anthropic API 调用失败: {type(e).__name__}: {e}", file=sys.stderr)
            return None

    # Fallback: OpenAI 兼容接口
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key='sk-dummy',
            base_url=os.environ.get('AI_BASE_URL', 'http://localhost:20128/v1')
        )
        resp = client.chat.completions.create(
            model=os.environ.get('AI_MODEL', 'Hermes'),
            max_tokens=max_tokens,
            stream=False,
            messages=[
                {"role": "system", "content": "你是求职偏好分析助手。请严格按 JSON 数组格式输出，不要输出其他内容。"},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except ImportError:
        print("⚠️  openai 库未安装", file=sys.stderr)
    except Exception as e:
        print(f"❌ OpenAI API 调用失败: {type(e).__name__}: {e}", file=sys.stderr)
    return None


def _parse_rules(text):
    """从 LLM 响应中解析 JSON 数组规则。返回 [(category, rule_value), ...]。"""
    if not text:
        return []
    try:
        start = text.find('[')
        end = text.rfind(']') + 1
        if start >= 0 and end > start:
            arr = json.loads(text[start:end])
            rules = []
            for item in arr:
                cat = item.get('category', '').strip()
                val = item.get('rule_value', '').strip()
                if cat in POSITIVE_CATEGORIES and val:
                    rules.append((cat, val))
            return rules
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️ JSON 解析失败: {e}")
    return []


def _upsert_memory_rule(conn, category, rule_value, raw_feedback=""):
    """写入一条 memory 规则，按 (category, rule_value) 去重。返回是否新增。"""
    c = conn.cursor()
    c.execute(
        "SELECT id FROM memories WHERE category = ? AND rule_value = ?",
        (category, rule_value)
    )
    if c.fetchone():
        return False
    c.execute(
        "INSERT INTO memories (category, rule_value, raw_feedback, created_at) "
        "VALUES (?, ?, ?, datetime('now'))",
        (category, rule_value, raw_feedback)
    )
    return True


def main():
    parser = argparse.ArgumentParser(description='从历史 approve 批量归纳正向偏好规则')
    parser.add_argument('--force', action='store_true', help='强制重新归纳（忽略指纹缓存）')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'批量大小（默认 {DEFAULT_BATCH_SIZE}）')
    parser.add_argument('--dry-run', action='store_true', help='仅预览归纳结果，不写库')
    args = parser.parse_args()

    profile = load_profile()
    if not profile:
        print("⚠️  未找到 profile，归纳质量会受限。")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    apps = get_approved_applications(conn)
    if not apps:
        print("✅ 没有已 approve 的 application，无需归纳。")
        conn.close()
        return

    approve_ids = [a['id'] for a in apps]
    current_fp = compute_fingerprint(approve_ids, profile)
    last_fp = load_last_fingerprint()

    if not args.force and current_fp == last_fp:
        print(f"ℹ️  approve 列表与 profile 自上次归纳以来未变化（指纹={current_fp[:8]}...），跳过 LLM 归纳。")
        print(f"    如需强制重新归纳，请加 --force。")
        conn.close()
        return

    print(f"📊 待归纳 approve 记录: {len(apps)} 条")
    print(f"   批量大小: {args.batch_size} | dry-run: {args.dry_run}")

    if args.dry_run:
        print("🔍 Dry-run 模式，仅预览：")
        for a in apps[:10]:
            print(f"  [{a['id']}] {a.get('company_name') or '-'} | {a.get('position') or '-'} | {a.get('industry') or '-'}")
        if len(apps) > 10:
            print(f"  ... 还有 {len(apps) - 10} 条")
        print("（dry-run 不调用 LLM，不写库）")
        conn.close()
        return

    total_rules = 0
    new_rules = 0
    batch_size = max(1, args.batch_size)
    total_batches = (len(apps) + batch_size - 1) // batch_size

    for batch_start in range(0, len(apps), batch_size):
        batch = apps[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        print(f"\n🔄 批次 {batch_num}/{total_batches}（{len(batch)} 条）")

        prompt = INDUCTION_PROMPT.format(
            profile=profile or "（未提供）",
            n=len(batch),
            apps_block=_format_batch_block(batch),
        )
        response = _call_llm(prompt)
        rules = _parse_rules(response)

        if not rules:
            print(f"  ⚠️ 本批次未提取到规则（LLM 返回为空或解析失败）")
            continue

        print(f"  提取到 {len(rules)} 条规则:")
        for cat, val in rules:
            is_new = _upsert_memory_rule(conn, cat, val, raw_feedback="批量归纳自 approve 记录")
            conn.commit()
            total_rules += 1
            if is_new:
                new_rules += 1
            flag = "新增" if is_new else "已存在"
            print(f"    [{flag}] {cat}: {val}")

    # 保存指纹（仅当实际调用了 LLM）
    save_fingerprint(current_fp)
    print(f"\n✅ 完成！归纳规则 {total_rules} 条，其中新增 {new_rules} 条，已存在 {total_rules - new_rules} 条")
    print(f"💾 已保存归纳指纹: {current_fp[:8]}...")
    conn.close()


if __name__ == '__main__':
    main()
