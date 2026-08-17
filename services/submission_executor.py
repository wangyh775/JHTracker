"""Submission Executor：网申预填执行器。

Phase 1（当前）：dry_run 模式 — 不启动 Playwright，接收传入的表单字段列表，
   逐字段经 SafetyGuard 分类 + 查 AnswerBank / 解析 profile 组装预填 JSON。
   写入 ApplicationSubmission 表 + 切换 Application 状态 待投递 → 待提交。

Phase 2（后续）：real 模式 — 用 Playwright 真实打开页面预填（不点提交），
   截图存证，CAPTCHA/登录态检测后切 awaiting_human。

Phase 2 之后再开 ThreadPoolExecutor 异步执行。

参考：
- openspec/changes/application-executor-semiauto/specs/submission-prefill/spec.md
- openspec/changes/application-executor-semiauto/design.md
"""
import json
import os
import re
import sqlite3
from datetime import datetime

from constants import (
    PROFILE_SENSITIVE_KEYS,
    PLAYWRIGHT_TIMEOUT,
)
from services.safety_guard import (
    classify_field,
    is_sensitive_category,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'tracker.db')
PROFILE_PATH = os.path.join(BASE_DIR, 'data', 'profile.md')
SUBMISSIONS_DIR = os.path.join(BASE_DIR, 'data', 'submissions')


# ============================================================
# Phase 2 异步执行器（占位，Phase 1 不启用）
# ============================================================
# from concurrent.futures import ThreadPoolExecutor
# _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='prefill')


# ============================================================
# profile.md 解析：把 Markdown 形式画像解析为 key-value 字典
# ============================================================
# 识别 - key: value 与 **Key**: value 与 ## 标题下的简单字段
# 首字符支持中英文，后续字符允许中文/字母/数字/下划线/连字符/空格
_PROFILE_KV_RE = re.compile(r'^[\-\*]?\s*\*{0,2}([\w\u4e00-\u9fa5][\w\u4e00-\u9fa5\- ]{0,40})\*{0,2}\s*[:：]\s*(.+?)\s*$')


def parse_profile_to_dict(profile_content):
    """粗略把 profile.md 解析为 {field: value} 字典，用于敏感字段取答案。

    支持格式：
      - 期望薪资: 25k
      - **期望薪资**: 25k
      - target_salary: 25000

    字段名归一化为 lower-snake（去空格、转小写）。
    """
    result = {}
    if not profile_content:
        return result
    for line in profile_content.splitlines():
        m = _PROFILE_KV_RE.match(line)
        if not m:
            continue
        key = m.group(1).strip().lower().replace(' ', '_').replace('-', '_')
        val = m.group(2).strip().strip('*').strip()
        if key and val:
            result[key] = val
    return result


def _lookup_profile_sensitive(profile_dict, category):
    """按敏感分类从 profile_dict 取值。返回 (value, matched_key) 或 (None, None)。

    PROFILE_SENSITIVE_KEYS 中存的是 ASCII key（如 target_salary）。
    profile.md 也可能用中文字段名，故按 key 精确匹配失败时，
    再做一轮「ASCII key 的中文等价名」匹配。
    """
    # 中文字段名候选（按敏感分类）：用户可能用中文写画像
    _ZH_ALIASES = {
        'identity': ['身份证号', '身份证', '护照号', '护照'],
        'legal': ['签证状态', '签证', '工作授权', '犯罪记录'],
        'compensation': ['期望薪资', '期望薪酬', '当前薪资', '目标薪资', '目标薪酬'],
        'current_status': ['现任雇主', '目前在职', '在职状态', '推荐人', '推荐人姓名'],
        'financial': ['银行账号', '银行卡号', '社保号', '公积金号'],
    }
    keys = list(PROFILE_SENSITIVE_KEYS.get(category, [])) + _ZH_ALIASES.get(category, [])
    for k in keys:
        norm_k = k.strip().lower().replace(' ', '_').replace('-', '_')
        if norm_k in profile_dict and profile_dict[norm_k]:
            return profile_dict[norm_k], norm_k
        # 也尝试原始 key（未归一化的中文）
        if k in profile_dict and profile_dict[k]:
            return profile_dict[k], k
    return None, None


# ============================================================
# AnswerBank 查询（Phase 1 走 sqlite3，跟 mcp_server 一致风格）
# ============================================================
def _query_answer_bank(conn, question, role_family=None):
    """查 AnswerBank，返回最匹配的答案。

    优先级：
    1. role_family 精确匹配 + question_pattern 模糊匹配（子串）
    2. role_family=NULL 通用 + question_pattern 模糊匹配
    3. 任意 role_family + question_pattern 匹配（兜底）

    返回 (answer, source) 或 (None, None)。
    source ∈ {'answer_bank', 'answer_bank_needs_review'}。
    """
    if not question:
        return None, None
    q = question.strip()
    # 1. role_family 精确 + question 模糊
    if role_family:
        rows = conn.execute(
            "SELECT answer, needs_review FROM answer_bank "
            "WHERE role_family = ? AND question_pattern LIKE ? "
            "ORDER BY needs_review ASC, id DESC LIMIT 1",
            (role_family, f'%{q}%')
        ).fetchall()
        if rows:
            return rows[0]['answer'], 'answer_bank_needs_review' if rows[0]['needs_review'] else 'answer_bank'

    # 2. 通用 + question 模糊
    rows = conn.execute(
        "SELECT answer, needs_review FROM answer_bank "
        "WHERE role_family IS NULL AND question_pattern LIKE ? "
        "ORDER BY needs_review ASC, id DESC LIMIT 1",
        (f'%{q}%',)
    ).fetchall()
    if rows:
        return rows[0]['answer'], 'answer_bank_needs_review' if rows[0]['needs_review'] else 'answer_bank'

    # 3. 兜底：任意 role_family
    rows = conn.execute(
        "SELECT answer, needs_review FROM answer_bank "
        "WHERE question_pattern LIKE ? "
        "ORDER BY needs_review ASC, id DESC LIMIT 1",
        (f'%{q}%',)
    ).fetchall()
    if rows:
        return rows[0]['answer'], 'answer_bank_needs_review' if rows[0]['needs_review'] else 'answer_bank'

    return None, None


# ============================================================
# Phase 1: prefill_dry_run
# ============================================================
def prefill_dry_run(application_id, form_url, fields, role_family=None, profile_content=None, task_id=None):
    """Phase 1 MVP：不启动 Playwright，按传入的 fields 列表组装 prefilled_data JSON。

    Args:
        application_id: Application.id
        form_url: 目标网申表单 URL
        fields: list of dict，每个 dict 至少含一个识别线索：
            { 'label': '期望薪资', 'name': 'salary', 'id': 'salary', 'placeholder': '...' }
            可选 'value' 直接给答案（人工传入）。
        role_family: 岗位族归一化字符串（可空）
        profile_content: profile.md 内容（可空，函数内部会读）
        task_id: Agent 任务 ID（可空）

    Returns:
        dict: { submission_id, status, prefilled_data, awaiting_human_items }
            status ∈ {'prefilled', 'awaiting_human', 'failed'}
    """
    if not form_url:
        return {'status': 'failed', 'reason': 'form_url is required'}

    if profile_content is None:
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                profile_content = f.read()
        else:
            profile_content = ''

    profile_dict = parse_profile_to_dict(profile_content)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # 校验 application 存在且当前在 待投递 状态（仅允许 Agent 在 STAGED 区间写）
        row = conn.execute(
            "SELECT id, status FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if not row:
            return {'status': 'failed', 'reason': f'application {application_id} not found'}
        if row['status'] not in ('待投递', '待提交'):
            return {
                'status': 'failed',
                'reason': f"application current status={row['status']!r} not in ('待投递','待提交')"
            }

        processed_fields = []
        awaiting_human_items = []
        has_awaiting = False

        for f in fields or []:
            label = f.get('label', '') or ''
            name = f.get('name', '') or ''
            id_attr = f.get('id', '') or ''
            placeholder = f.get('placeholder', '') or ''
            category = classify_field(label_text=label, name=name, id_attr=id_attr, placeholder=placeholder)

            # 人工直接传答案 → 优先采用
            if 'value' in f and f['value'] is not None:
                processed_fields.append({
                    'selector': {'label': label, 'name': name, 'id': id_attr, 'placeholder': placeholder},
                    'classified_as': category,
                    'answer': str(f['value']),
                    'source': 'human_filled',
                    'filled': True,
                })
                continue

            # 敏感字段 → 从 profile 取
            if is_sensitive_category(category):
                value, matched_key = _lookup_profile_sensitive(profile_dict, category)
                if value:
                    processed_fields.append({
                        'selector': {'label': label, 'name': name, 'id': id_attr, 'placeholder': placeholder},
                        'classified_as': category,
                        'answer': value,
                        'source': 'profile',
                        'profile_key': matched_key,
                        'filled': True,
                    })
                else:
                    processed_fields.append({
                        'selector': {'label': label, 'name': name, 'id': id_attr, 'placeholder': placeholder},
                        'classified_as': category,
                        'answer': None,
                        'source': 'missing',
                        'filled': False,
                    })
                    has_awaiting = True
                    awaiting_human_items.append(f"敏感字段[{category}]「{label or name or id_attr or placeholder}」缺失，请补填")
                continue

            # 非敏感字段 → 查 AnswerBank
            question = label or name or id_attr or placeholder
            answer, source = _query_answer_bank(conn, question, role_family=role_family)
            if answer is not None:
                processed_fields.append({
                    'selector': {'label': label, 'name': name, 'id': id_attr, 'placeholder': placeholder},
                    'classified_as': category,
                    'answer': answer,
                    'source': source,
                    'filled': True,
                })
            else:
                processed_fields.append({
                    'selector': {'label': label, 'name': name, 'id': id_attr, 'placeholder': placeholder},
                    'classified_as': category,
                    'answer': None,
                    'source': 'missing',
                    'filled': False,
                })
                has_awaiting = True
                awaiting_human_items.append(f"非敏感字段「{label or name or id_attr or placeholder}」AnswerBank 未命中，请补填")

        submission_status = 'awaiting_human' if has_awaiting else 'prefilled'
        prefilled_data = {
            'fields': processed_fields,
            'role_family': role_family,
            'awaiting_human_items': awaiting_human_items,
        }
        prefilled_json = json.dumps(prefilled_data, ensure_ascii=False)

        # 写 ApplicationSubmission（同一 application 可能有多条历史，按 id DESC 取最新）
        conn.execute(
            "INSERT INTO application_submissions "
            "(application_id, form_url, prefilled_data, agent_trace_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (application_id, form_url, prefilled_json, task_id, submission_status)
        )
        submission_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()['id']

        # 切换 application 状态：待投递 → 待提交（已处于待提交则保持）
        if row['status'] == '待投递':
            conn.execute(
                "UPDATE applications SET status = '待提交', updated_at = datetime('now') WHERE id = ?",
                (application_id,)
            )

        # 写 AgentEvent 轨迹（若 task_id 提供）
        if task_id:
            conn.execute(
                "INSERT INTO agent_events (task_id, event_type, payload_json, created_at) "
                "SELECT id, ?, ?, datetime('now') FROM agent_tasks WHERE task_id = ?",
                (
                    'prefill_dry_run_done',
                    json.dumps({'submission_id': submission_id, 'status': submission_status,
                                'awaiting_count': len(awaiting_human_items)}, ensure_ascii=False),
                    task_id
                )
            )

        conn.commit()

        return {
            'submission_id': submission_id,
            'status': submission_status,
            'application_status': '待提交',
            'prefilled_data': prefilled_data,
            'awaiting_human_items': awaiting_human_items,
        }
    finally:
        conn.close()


def record_submission(application_id, success, screenshot_path=None, failure_reason=None, extracted_answers=None):
    """人类在真实页面提交后，由 Agent 或 Web 调用回写最终结果。

    Args:
        application_id: Application.id
        success: True=已成功提交 → 状态变 已投递；False=失败 → 回退 待投递
        screenshot_path: 人类提交后的截图路径（可空）
        failure_reason: 失败原因（success=False 时填）
        extracted_answers: list of {question, answer, role_family, classified_as}
            Phase 3 才会真正调 upsert_answer_bank 沉淀；Phase 1 仅留 TODO。

    Returns:
        dict: { application_id, application_status, submission_status }
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT id, status FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if not row:
            return {'status': 'failed', 'reason': f'application {application_id} not found'}

        # 拿最新一条 ApplicationSubmission
        sub = conn.execute(
            "SELECT id, status FROM application_submissions "
            "WHERE application_id = ? ORDER BY id DESC LIMIT 1",
            (application_id,)
        ).fetchone()

        if success:
            # application: 待提交 → 已投递；写 apply_date
            conn.execute(
                "UPDATE applications SET status = '已投递', apply_date = CURRENT_DATE, updated_at = datetime('now') "
                "WHERE id = ?",
                (application_id,)
            )
            if sub:
                conn.execute(
                    "UPDATE application_submissions SET status = 'submitted', "
                    "submitted_at = datetime('now'), human_approved_at = datetime('now'), "
                    "screenshot_path = ?, updated_at = datetime('now') WHERE id = ?",
                    (screenshot_path, sub['id'])
                )
            submission_status = 'submitted'
            application_status = '已投递'
        else:
            # application: 待提交 → 待投递（回退）
            conn.execute(
                "UPDATE applications SET status = '待投递', updated_at = datetime('now') WHERE id = ?",
                (application_id,)
            )
            if sub:
                conn.execute(
                    "UPDATE application_submissions SET status = 'failed', failure_reason = ?, "
                    "updated_at = datetime('now') WHERE id = ?",
                    (failure_reason, sub['id'])
                )
            submission_status = 'failed'
            application_status = '待投递'

        # Phase 3 TODO: 自动沉淀 extracted_answers 到 AnswerBank（needs_review=1, source='extracted'）
        # 当前 Phase 1 仅留参数入口，不实装。
        _ = extracted_answers  # noqa: F841

        conn.commit()
        return {
            'status': 'success',
            'application_id': application_id,
            'application_status': application_status,
            'submission_status': submission_status,
        }
    finally:
        conn.close()
