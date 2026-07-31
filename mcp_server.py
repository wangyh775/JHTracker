"""JHTracker MCP Server — Exposes career memory resources and tools for AI agents via Model Context Protocol."""
import os
import json
import sqlite3
from mcp.server.fastmcp import FastMCP
from constants import (
    memory_polarity,
    MEMORY_CATEGORIES_POSITIVE,
    MEMORY_CATEGORIES_NEGATIVE,
)

# Initialize FastMCP Server
mcp = FastMCP("JHTracker")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'tracker.db')
PROFILE_PATH = os.path.join(BASE_DIR, 'data', 'profile.md')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


@mcp.resource("jhtracker://profile")
def get_candidate_profile() -> str:
    """Read the candidate career profile and preferences."""
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return "No candidate profile found."


@mcp.tool()
def search_companies(query: str = "") -> str:
    """Search target companies by name, industry, or match reason."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if query.strip():
            sql = """
                SELECT id, name, city, industry, priority, score, score_reason
                FROM companies
                WHERE name LIKE ? OR match_reason LIKE ? OR industry LIKE ?
                ORDER BY score DESC NULLS LAST, id DESC
                LIMIT 20
            """
            q_param = f"%{query.strip()}%"
            cursor.execute(sql, (q_param, q_param, q_param))
        else:
            sql = """
                SELECT id, name, city, industry, priority, score, score_reason
                FROM companies
                ORDER BY score DESC NULLS LAST, id DESC
                LIMIT 20
            """
            cursor.execute(sql)

        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return json.dumps({'status': 'success', 'count': len(results), 'companies': results}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def update_company_score(company_id: int, score: int, reason: str = "") -> str:
    """Update company AI score (0-100) and evaluation score_reason."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE companies SET score = ?, score_reason = ? WHERE id = ?", (score, reason, company_id))
        conn.commit()
        if cursor.rowcount > 0:
            return json.dumps({'status': 'success', 'company_id': company_id, 'score': score, 'score_reason': reason}, ensure_ascii=False)
        return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def create_company(
    name: str,
    industry: str = None,
    city: str = None,
    priority: str = None,
    website: str = None,
    match_reason: str = None,
    score: int = None,
    score_reason: str = None
) -> str:
    """Create a new company record with automatic deduplication. If company name already exists, returns existing company details."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM companies WHERE LOWER(name) = LOWER(?)", (name.strip(),))
        row = cursor.fetchone()
        if row:
            return json.dumps({
                'status': 'success',
                'created': False,
                'company': {'id': row['id'], 'name': row['name']}
            }, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO companies (name, industry, city, priority, website, match_reason, score, score_reason, source_list, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MCP Auto-Sourcing', datetime('now'))
        """, (name.strip(), industry, city, priority, website, match_reason, score, score_reason))
        conn.commit()
        company_id = cursor.lastrowid
        return json.dumps({
            'status': 'success',
            'created': True,
            'company': {'id': company_id, 'name': name.strip()}
        }, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def create_application(
    company_id: int,
    position: str = "待定岗位",
    job_desc: str = None,
    url: str = None,
    channel: str = "MCP 自动推送",
    match_score: int = None,
    agent_reason: str = None,
    agent_task_id: str = None,
    source_url: str = None,
    resume_id: int = None
) -> str:
    """Create a new job application record under specified company with default 'Pending Approval' status, resume version binding, and HITL recommendation metadata."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM companies WHERE id = ?", (company_id,))
        comp = cursor.fetchone()
        if not comp:
            return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO applications (company_id, position, status, channel, job_desc, url, match_score, agent_reason, agent_task_id, source_url, resume_id, created_at, updated_at)
            VALUES (?, ?, 'Pending Approval', ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (company_id, position, channel, job_desc, url, match_score, agent_reason, agent_task_id, source_url, resume_id))
        conn.commit()
        app_id = cursor.lastrowid
        return json.dumps({
            'status': 'success',
            'application': {
                'id': app_id,
                'company_id': company_id,
                'company_name': comp['name'],
                'position': position,
                'status': 'Pending Approval',
                'url': url,
                'match_score': match_score,
                'agent_reason': agent_reason,
                'agent_task_id': agent_task_id,
                'source_url': source_url,
                'resume_id': resume_id
            }
        }, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def get_user_preferences() -> str:
    """Get candidate career profile, positive preference rules, negative constraint rules,
    and recent human rejection notes."""
    conn = get_db_connection()
    try:
        profile_content = ""
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                profile_content = f.read()

        cursor = conn.cursor()
        cursor.execute("SELECT category, rule_value, raw_feedback FROM memories ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()

        positive_rules = []
        negative_rules = []
        recent_rejection_notes = []

        for row in rows:
            polarity = memory_polarity(row['category'])
            if row['rule_value']:
                entry = {'category': row['category'], 'rule_value': row['rule_value']}
                if polarity == 'positive':
                    positive_rules.append(entry)
                else:
                    negative_rules.append(entry)
            if row['raw_feedback']:
                recent_rejection_notes.append(row['raw_feedback'])

        return json.dumps({
            'status': 'success',
            'profile': profile_content,
            'positive_rules': positive_rules,
            'negative_rules': negative_rules,
            'recent_rejection_notes': recent_rejection_notes[:20]
        }, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def evaluate_jd(
    jd_text: str,
    company_name: str = "",
    task_id: str = None
) -> str:
    """Evaluate Job Description (JD) text against candidate profile, positive preference rules,
    and negative constraint rules. Returns match score, positive highlights, potential risks/weaknesses,
    and logs an Agent trace.
    """
    import uuid
    if not task_id:
        task_id = f"eval-{uuid.uuid4().hex[:8]}"

    conn = get_db_connection()
    try:
        profile_content = ""
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                profile_content = f.read().lower()

        score, highlights, risks, positive_matches, negative_matches, rejection_warnings = _evaluate_jd_inner(
            conn, jd_text, profile_content
        )

        final_score = min(max(score, 0), 100)
        reason = f"最终评估得分 {final_score} 分。亮点: {'; '.join(highlights) or '综合符合基准要求'}。"
        if risks:
            reason += f" 风险提示: {'; '.join(risks)}。"

        result_payload = {
            'task_id': task_id,
            'company_name': company_name,
            'match_score': final_score,
            'highlights': highlights,
            'risks': risks,
            'positive_matches': positive_matches,
            'negative_matches': negative_matches,
            'rejection_warnings': rejection_warnings,
            'reason': reason
        }
        record_agent_trace(task_id=task_id, agent_name="JD-Evaluator", event_type="evaluation_result", payload=result_payload, status="completed")
        return json.dumps({'status': 'success', 'result': result_payload}, ensure_ascii=False)
    finally:
        conn.close()


def _evaluate_jd_inner(conn, jd_text: str, profile_content: str = ""):
    """JD 评估核心逻辑（被 evaluate_jd 与 batch_evaluate_jds 共用）。

    消费双向 memory 规则：
      正向（prefer_* / salary_expected）命中 → 加分 + highlights
      负向（exclude_* / salary_too_low / general）命中 → 扣分 + risks
      历史 reject feedback 分词命中 → 扣分 + risks

    返回 (score, highlights, risks, positive_matches, negative_matches, rejection_warnings)。
    """
    cursor = conn.cursor()
    # 正向规则
    cursor.execute(
        "SELECT category, rule_value FROM memories "
        "WHERE category IN ('prefer_tech','prefer_domain','prefer_company','salary_expected','culture_fit') "
        "AND rule_value IS NOT NULL AND rule_value != ''"
    )
    positive_rows = cursor.fetchall()
    # 负向规则
    cursor.execute(
        "SELECT category, rule_value FROM memories "
        "WHERE category IN ('exclude_tech','exclude_company','salary_too_low','general') "
        "AND rule_value IS NOT NULL AND rule_value != ''"
    )
    negative_rows = cursor.fetchall()
    # 历史 reject feedback
    cursor.execute(
        "SELECT raw_feedback FROM decision_feedbacks "
        "WHERE action = 'reject' AND raw_feedback IS NOT NULL AND raw_feedback != '' "
        "ORDER BY id DESC LIMIT 20"
    )
    feedback_rows = cursor.fetchall()

    jd_lower = jd_text.lower()

    positive_matches = []
    for row in positive_rows:
        rule_val = row['rule_value'].lower()
        if rule_val and rule_val in jd_lower:
            positive_matches.append(row['rule_value'])

    negative_matches = []
    for row in negative_rows:
        rule_val = row['rule_value'].lower()
        if rule_val and rule_val in jd_lower:
            negative_matches.append(row['rule_value'])

    rejection_warnings = []
    for f_row in feedback_rows:
        raw_text = f_row['raw_feedback'].strip()
        if raw_text and any(word in jd_lower for word in raw_text.lower().split() if len(word) > 1):
            if raw_text not in rejection_warnings:
                rejection_warnings.append(raw_text)

    score = 75
    highlights = []
    risks = []

    # 正向加分：每条 +4，上限 +20
    if positive_matches:
        score += min(len(positive_matches) * 4, 20)
        highlights.append(f"匹配用户偏好规则: {', '.join(positive_matches[:5])}")

    # 负向扣分
    if negative_matches:
        score = max(score - len(negative_matches) * 15, 10)
        risks.append(f"触发负向偏好排查规则: {', '.join(negative_matches)}")

    if rejection_warnings:
        score = max(score - min(len(rejection_warnings) * 10, 30), 10)
        risks.append(f"匹配过往拒绝反馈特征: {'; '.join(rejection_warnings[:3])}")

    if "外包" in jd_lower or "驻场" in jd_lower:
        score = min(score, 30)
        risks.append("岗位包含外包/驻场特征关键词")

    return score, highlights, risks, positive_matches, negative_matches, rejection_warnings


@mcp.tool()
def update_candidate_profile(content: str) -> str:
    """Update candidate career profile Markdown content in data/profile.md."""
    try:
        os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
        with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({'status': 'success', 'message': 'Candidate profile updated successfully'}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)


@mcp.tool()
def record_agent_trace(
    task_id: str,
    agent_name: str = "Agent",
    event_type: str = "info",
    payload: dict = None,
    status: str = "running"
) -> str:
    """Record or update an AgentTask and append an AgentEvent trace in SQLite database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM agent_tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            cursor.execute(
                "INSERT INTO agent_tasks (task_id, agent_name, status, created_at) VALUES (?, ?, ?, datetime('now'))",
                (task_id, agent_name, status)
            )
            db_task_id = cursor.lastrowid
        else:
            db_task_id = row['id']
            cursor.execute(
                "UPDATE agent_tasks SET status = ?, agent_name = ? WHERE id = ?",
                (status, agent_name, db_task_id)
            )

        payload_json = json.dumps(payload or {}, ensure_ascii=False)
        cursor.execute(
            "INSERT INTO agent_events (task_id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))",
            (db_task_id, event_type, payload_json)
        )
        conn.commit()
        event_id = cursor.lastrowid

        return json.dumps({
            'status': 'success',
            'task_id': task_id,
            'db_task_id': db_task_id,
            'event_id': event_id
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)
    finally:
        conn.close()


if __name__ == '__main__':
    mcp.run()


# ============================================================
# Company Domain Tools
# ============================================================


@mcp.tool()
def get_company(company_id: int) -> str:
    """Get full company details with application count and note count."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)
        company = dict(row)
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE company_id = ?", (company_id,))
        company['application_count'] = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM notes WHERE company_id = ?", (company_id,))
        company['note_count'] = cursor.fetchone()['cnt']
        return json.dumps({'status': 'success', 'company': company}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def update_company(
    company_id: int,
    name: str = None,
    industry: str = None,
    city: str = None,
    sub_city: str = None,
    job_type: str = None,
    match_reason: str = None,
    priority: str = None,
    website: str = None,
    salary_min: int = None,
    salary_max: int = None,
    scale: str = None,
    financing_stage: str = None,
    tags: str = None,
    company_type: str = None
) -> str:
    """Update editable company fields. Only provided fields are updated."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)

        fields = []
        params = []
        for key, val in [('name', name), ('industry', industry), ('city', city),
                         ('sub_city', sub_city), ('job_type', job_type),
                         ('match_reason', match_reason), ('priority', priority),
                         ('website', website), ('salary_min', salary_min),
                         ('salary_max', salary_max), ('scale', scale),
                         ('financing_stage', financing_stage), ('tags', tags),
                         ('company_type', company_type)]:
            if val is not None:
                fields.append(f"{key} = ?")
                params.append(val)
        if not fields:
            return json.dumps({'status': 'error', 'message': 'No fields to update'}, ensure_ascii=False)
        params.append(company_id)
        cursor.execute(f"UPDATE companies SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
        return json.dumps({'status': 'success', 'company_id': company_id}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def delete_company(company_id: int, confirm: bool = False) -> str:
    """Delete a company and all associated applications and notes. Requires confirm=True."""
    if not confirm:
        return json.dumps({'status': 'error', 'message': 'Confirmation required. Set confirm=True to delete.'}, ensure_ascii=False)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)
        cursor.execute("DELETE FROM applications WHERE company_id = ?", (company_id,))
        cursor.execute("DELETE FROM notes WHERE company_id = ?", (company_id,))
        cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        conn.commit()
        return json.dumps({'status': 'success', 'message': 'Company deleted'}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Application Domain Tools
# ============================================================


@mcp.tool()
def get_application(application_id: int) -> str:
    """Get application detail with company name, resume name, and interview feedbacks."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, c.name AS company_name, r.name AS resume_name
            FROM applications a
            LEFT JOIN companies c ON c.id = a.company_id
            LEFT JOIN resumes r ON r.id = a.resume_id
            WHERE a.id = ?
        """, (application_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({'status': 'error', 'message': 'Application not found'}, ensure_ascii=False)
        app = dict(row)
        cursor.execute("SELECT * FROM interview_feedbacks WHERE application_id = ? ORDER BY id ASC", (application_id,))
        app['feedbacks'] = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM decision_feedbacks WHERE application_id = ? ORDER BY id DESC LIMIT 5", (application_id,))
        app['decision_feedbacks'] = [dict(r) for r in cursor.fetchall()]
        return json.dumps({'status': 'success', 'application': app}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def list_applications(status: str = None, company_id: int = None, channel: str = None, limit: int = 50) -> str:
    """List applications with optional filtering by status, company_id, or channel."""
    conn = get_db_connection()
    try:
        conditions = []
        params = []
        if status:
            conditions.append("a.status = ?")
            params.append(status)
        if company_id:
            conditions.append("a.company_id = ?")
            params.append(company_id)
        if channel:
            conditions.append("a.channel = ?")
            params.append(channel)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT a.*, c.name AS company_name
            FROM applications a
            LEFT JOIN companies c ON c.id = a.company_id
            {where}
            ORDER BY a.id DESC LIMIT ?
        """, params + [limit])
        rows = cursor.fetchall()
        return json.dumps({'status': 'success', 'count': len(rows), 'applications': [dict(r) for r in rows]}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def update_application_status(application_id: int, status: str) -> str:
    """Update application status (e.g., 已投递, 简历筛选, 笔试, 一面, 二面, 终面, Offer, 已拒)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET status = ?, updated_at = datetime('now') WHERE id = ?", (status, application_id))
        conn.commit()
        if cursor.rowcount == 0:
            return json.dumps({'status': 'error', 'message': 'Application not found'}, ensure_ascii=False)
        return json.dumps({'status': 'success', 'application_id': application_id, 'status': status}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def get_pending_approvals() -> str:
    """Get all applications pending human approval."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, c.name AS company_name, r.name AS resume_name
            FROM applications a
            LEFT JOIN companies c ON c.id = a.company_id
            LEFT JOIN resumes r ON r.id = a.resume_id
            WHERE a.status IN ('Pending Approval', '待审批', '待投递')
            ORDER BY a.id DESC
        """)
        rows = cursor.fetchall()
        return json.dumps({'status': 'success', 'count': len(rows), 'proposals': [dict(r) for r in rows]}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def handle_decision(
    application_id: int,
    action: str,
    reason_category: str = "general",
    raw_feedback: str = "",
    rule_value: str = "",
    position: str = None,
    resume_id: int = None
) -> str:
    """Handle human decision on a pending proposal. action: approve, reject, or edit.

    approve → 写正向记忆（prefer_* / salary_expected），从关联 company/position 提取结构化特征
    reject  → 写负向记忆（exclude_* / salary_too_low / general），rule_value 仅存结构化值
    edit    → 仅更新字段 + 记录 feedback，不写 memory
    """
    if action not in ('approve', 'reject', 'edit'):
        return json.dumps({'status': 'error', 'message': "Action must be 'approve', 'reject', or 'edit'"}, ensure_ascii=False)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM applications WHERE id = ?", (application_id,))
        if not cursor.fetchone():
            return json.dumps({'status': 'error', 'message': 'Application not found'}, ensure_ascii=False)

        if action == 'approve':
            cursor.execute("UPDATE applications SET status = 'Applied', updated_at = datetime('now') WHERE id = ?", (application_id,))
            cursor.execute(
                "INSERT INTO decision_feedbacks (application_id, action, reason_category, raw_feedback, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (application_id, action, reason_category, raw_feedback))
            # 写正向记忆：从关联 application/company/position 提取简单结构化特征
            positive_rules = _extract_positive_features(conn, application_id, rule_value)
            for cat, val in positive_rules:
                _upsert_memory_rule(conn, cat, val, raw_feedback, application_id=application_id)
        elif action == 'reject':
            cursor.execute("UPDATE applications SET status = 'Rejected', updated_at = datetime('now') WHERE id = ?", (application_id,))
            cursor.execute(
                "INSERT INTO decision_feedbacks (application_id, action, reason_category, raw_feedback, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (application_id, action, reason_category, raw_feedback))
            # 写负向记忆：rule_value 仅存结构化值（修复污染 bug），未传则留空待批量归纳补齐
            neg_category = reason_category if reason_category in (
                'exclude_tech', 'exclude_company', 'salary_too_low', 'general'
            ) else 'general'
            _upsert_memory_rule(conn, neg_category, rule_value, raw_feedback, application_id=application_id)
        elif action == 'edit':
            updates = ["updated_at = datetime('now')"]
            params = []
            if position is not None:
                updates.append("position = ?")
                params.append(position)
            if resume_id is not None:
                updates.append("resume_id = ?")
                params.append(resume_id)
            params.append(application_id)
            cursor.execute(f"UPDATE applications SET {', '.join(updates)} WHERE id = ?", params)
            cursor.execute(
                "INSERT INTO decision_feedbacks (application_id, action, reason_category, raw_feedback, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (application_id, action, reason_category, raw_feedback))
        conn.commit()
        return json.dumps({'status': 'success', 'action': action, 'application_id': application_id}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)
    finally:
        conn.close()


def _extract_positive_features(conn, application_id: int, explicit_rule_value: str = ""):
    """从关联 application + company 提取简单正向结构化特征。

    返回 [(category, rule_value), ...] 列表。无法提取时返回空列表。
    调用方传了 explicit_rule_value 则优先使用（视为 prefer_tech）。
    """
    rules = []
    if explicit_rule_value:
        rules.append(('prefer_tech', explicit_rule_value))
        return rules
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT a.position, a.job_desc, c.name AS company_name, c.industry "
            "FROM applications a LEFT JOIN companies c ON a.company_id = c.id "
            "WHERE a.id = ?",
            (application_id,)
        )
        row = cursor.fetchone()
        if not row:
            return rules
        company_name = row['company_name'] if row['company_name'] else None
        industry = row['industry'] if row['industry'] else None
        if company_name:
            rules.append(('prefer_company', company_name))
        if industry:
            rules.append(('prefer_domain', industry))
    except Exception:
        pass
    return rules


def _upsert_memory_rule(conn, category: str, rule_value: str, raw_feedback: str = "", application_id=None):
    """写入一条 memory 规则，按 (category, rule_value) 去重。

    rule_value 可为空（待批量归纳补齐），此时不参与去重检查（允许多条空值）。
    """
    cursor = conn.cursor()
    if rule_value:
        cursor.execute(
            "SELECT id FROM memories WHERE category = ? AND rule_value = ?",
            (category, rule_value)
        )
        if cursor.fetchone():
            return  # 已存在，跳过
    cursor.execute(
        "INSERT INTO memories (application_id, category, rule_value, raw_feedback, created_at) "
        "VALUES (?, ?, ?, ?, datetime('now'))",
        (application_id, category, rule_value, raw_feedback)
    )


@mcp.tool()
def archive_application(application_id: int, archive: bool = True) -> str:
    """Toggle application archived status."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        val = 1 if archive else 0
        cursor.execute("UPDATE applications SET is_archived = ?, archived_at = CASE WHEN ? THEN datetime('now') ELSE NULL END, updated_at = datetime('now') WHERE id = ?", (val, archive, application_id))
        conn.commit()
        if cursor.rowcount == 0:
            return json.dumps({'status': 'error', 'message': 'Application not found'}, ensure_ascii=False)
        return json.dumps({'status': 'success', 'application_id': application_id, 'is_archived': archive}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Interview Feedback Domain Tools
# ============================================================


@mcp.tool()
def create_interview_feedback(
    application_id: int,
    round: str = "一面",
    interviewer: str = "",
    interview_date: str = None,
    difficulty: int = 3,
    self_rating: int = 3,
    questions: str = "",
    improvement: str = ""
) -> str:
    """Create an interview feedback record for an application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM applications WHERE id = ?", (application_id,))
        if not cursor.fetchone():
            return json.dumps({'status': 'error', 'message': 'Application not found'}, ensure_ascii=False)
        cursor.execute("""
            INSERT INTO interview_feedbacks (application_id, interviewer, interview_date, round, difficulty, self_rating, questions, improvement, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (application_id, interviewer, interview_date, round, difficulty, self_rating, questions, improvement))
        conn.commit()
        return json.dumps({'status': 'success', 'feedback_id': cursor.lastrowid, 'application_id': application_id}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def list_interview_feedbacks(application_id: int) -> str:
    """List all interview feedbacks for an application."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interview_feedbacks WHERE application_id = ? ORDER BY id ASC", (application_id,))
        rows = cursor.fetchall()
        return json.dumps({'status': 'success', 'count': len(rows), 'feedbacks': [dict(r) for r in rows]}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Note Domain Tools
# ============================================================


@mcp.tool()
def create_note(company_id: int, title: str, content: str = "", category: str = "general") -> str:
    """Create a note for a company."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)
        cursor.execute("INSERT INTO notes (company_id, category, title, content, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                       (company_id, category, title, content))
        conn.commit()
        return json.dumps({'status': 'success', 'note_id': cursor.lastrowid}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def list_notes(company_id: int) -> str:
    """List all notes for a company."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE company_id = ? ORDER BY id DESC", (company_id,))
        rows = cursor.fetchall()
        return json.dumps({'status': 'success', 'count': len(rows), 'notes': [dict(r) for r in rows]}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def update_note(note_id: int, title: str = None, content: str = None, category: str = None) -> str:
    """Update a note's fields."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        fields = []
        params = []
        for key, val in [('title', title), ('content', content), ('category', category)]:
            if val is not None:
                fields.append(f"{key} = ?")
                params.append(val)
        if not fields:
            return json.dumps({'status': 'error', 'message': 'No fields to update'}, ensure_ascii=False)
        params.append(note_id)
        cursor.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
        if cursor.rowcount == 0:
            return json.dumps({'status': 'error', 'message': 'Note not found'}, ensure_ascii=False)
        return json.dumps({'status': 'success', 'note_id': note_id}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def delete_note(note_id: int, confirm: bool = False) -> str:
    """Delete a note. Requires confirm=True."""
    if not confirm:
        return json.dumps({'status': 'error', 'message': 'Confirmation required. Set confirm=True to delete.'}, ensure_ascii=False)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        return json.dumps({'status': 'success', 'message': 'Note deleted'}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Timeline Domain Tools
# ============================================================


@mcp.tool()
def create_timeline_event(event_date: str, title: str, description: str = "", event_type: str = "milestone", end_date: str = None) -> str:
    """Create a timeline event."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO timeline (event_date, end_date, title, description, event_type, done, created_at)
            VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
        """, (event_date, end_date, title, description, event_type))
        conn.commit()
        return json.dumps({'status': 'success', 'event_id': cursor.lastrowid}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def list_timeline_events() -> str:
    """List all upcoming timeline events."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timeline ORDER BY event_date ASC LIMIT 50")
        rows = cursor.fetchall()
        return json.dumps({'status': 'success', 'count': len(rows), 'events': [dict(r) for r in rows]}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def toggle_timeline_event(event_id: int) -> str:
    """Toggle the done status of a timeline event."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT done FROM timeline WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({'status': 'error', 'message': 'Event not found'}, ensure_ascii=False)
        new_done = 0 if row['done'] else 1
        cursor.execute("UPDATE timeline SET done = ? WHERE id = ?", (new_done, event_id))
        conn.commit()
        return json.dumps({'status': 'success', 'event_id': event_id, 'done': bool(new_done)}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Resume Domain Tools
# ============================================================


@mcp.tool()
def list_resumes() -> str:
    """List all resume versions."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, version, file_type, file_size, is_default, note, created_at FROM resumes ORDER BY id DESC")
        rows = cursor.fetchall()
        return json.dumps({'status': 'success', 'count': len(rows), 'resumes': [dict(r) for r in rows]}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def get_default_resume() -> str:
    """Get the default resume ID and name."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, version FROM resumes WHERE is_default = 1 LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return json.dumps({'status': 'success', 'resume': None}, ensure_ascii=False)
        return json.dumps({'status': 'success', 'resume': dict(row)}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Memory Rule Tools
# ============================================================


@mcp.tool()
def add_memory_rule(category: str, rule_value: str, raw_feedback: str = "", polarity: str = "") -> str:
    """Add a memory rule. Supports both positive (prefer_*) and negative (exclude_*) rules.

    polarity: 'positive' / 'negative' / '' (empty = use category as-is, backward compatible).
    When polarity is set, validates/maps category to the correct prefix:
      - polarity='positive' + category='tech' → 'prefer_tech'
      - polarity='negative' + category='tech' → 'exclude_tech'
      - Full category names (e.g. 'prefer_company', 'salary_too_low') are accepted as-is if they match polarity.
    Writes are deduplicated by (category, rule_value).
    """
    final_category = _resolve_memory_category(category, polarity)
    if not final_category:
        return json.dumps({
            'status': 'error',
            'message': f"Invalid category/polarity combination: category={category!r}, polarity={polarity!r}"
        }, ensure_ascii=False)

    conn = get_db_connection()
    try:
        _upsert_memory_rule(conn, final_category, rule_value, raw_feedback)
        conn.commit()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM memories WHERE category = ? AND rule_value = ? ORDER BY id DESC LIMIT 1",
                       (final_category, rule_value))
        row = cursor.fetchone()
        memory_id = row['id'] if row else None
        return json.dumps({
            'status': 'success',
            'memory_id': memory_id,
            'category': final_category,
            'polarity': memory_polarity(final_category)
        }, ensure_ascii=False)
    finally:
        conn.close()


def _resolve_memory_category(category: str, polarity: str):
    """根据 polarity 校验/映射 category，返回最终 category 或 None（非法组合）。"""
    category = (category or '').strip()
    polarity = (polarity or '').strip().lower()
    if not polarity:
        # 向后兼容：未传 polarity 时直接使用 category
        return category if category else None

    if polarity == 'positive':
        # 完整正向类别名直接接受
        if category in MEMORY_CATEGORIES_POSITIVE:
            return category
        # 短名映射：tech → prefer_tech
        mapped = f"prefer_{category}"
        if mapped in MEMORY_CATEGORIES_POSITIVE:
            return mapped
        # salary_expected 是正向例外
        if category == 'salary_expected':
            return category
        return None

    if polarity == 'negative':
        if category in MEMORY_CATEGORIES_NEGATIVE:
            return category
        mapped = f"exclude_{category}"
        if mapped in MEMORY_CATEGORIES_NEGATIVE:
            return mapped
        return None

    return None


@mcp.tool()
def delete_memory_rule(memory_id: int, confirm: bool = False) -> str:
    """Delete a memory rule. Requires confirm=True."""
    if not confirm:
        return json.dumps({'status': 'error', 'message': 'Confirmation required. Set confirm=True to delete.'}, ensure_ascii=False)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return json.dumps({'status': 'success', 'message': 'Memory rule deleted'}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Statistics Tool
# ============================================================


@mcp.tool()
def get_statistics() -> str:
    """Get dashboard-level aggregate statistics."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM companies")
        total_companies = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM companies WHERE priority = 'S'")
        s_count = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE status IN ('已投递','简历筛选','笔试','一面','二面','终面','Offer')")
        applied = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE status IN ('一面','二面','终面')")
        interviews = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE status = 'Offer'")
        offers = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE status = '已拒'")
        rejected = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE status IN ('Pending Approval','待审批','待投递')")
        pending_approvals = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE is_archived = 0")
        active_applications = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE is_archived = 1")
        archived_applications = cursor.fetchone()['cnt']
        return json.dumps({
            'status': 'success',
            'statistics': {
                'total_companies': total_companies,
                's_priority_companies': s_count,
                'applied': applied,
                'interviews': interviews,
                'offers': offers,
                'rejected': rejected,
                'pending_approvals': pending_approvals,
                'active_applications': active_applications,
                'archived_applications': archived_applications
            }
        }, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Trace & Task Tools
# ============================================================


@mcp.tool()
def list_agent_tasks(status: str = None, limit: int = 50) -> str:
    """List agent tasks with event counts and pending approvals count."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM applications WHERE status IN ('Pending Approval','待审批','待投递')")
        pending_count = cursor.fetchone()['cnt']
        if status:
            cursor.execute("""
                SELECT t.*, (SELECT COUNT(*) FROM agent_events WHERE task_id = t.id) AS event_count
                FROM agent_tasks t WHERE t.status = ? ORDER BY t.id DESC LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT t.*, (SELECT COUNT(*) FROM agent_events WHERE task_id = t.id) AS event_count
                FROM agent_tasks t ORDER BY t.id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        return json.dumps({
            'status': 'success',
            'count': len(rows),
            'pending_approvals_count': pending_count,
            'tasks': [dict(r) for r in rows]
        }, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def get_agent_task(task_id: str) -> str:
    """Get agent task detail with full event trace log."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_tasks WHERE task_id = ? OR id = ?", (task_id, task_id))
        row = cursor.fetchone()
        if not row:
            return json.dumps({'status': 'error', 'message': 'Task not found'}, ensure_ascii=False)
        task = dict(row)
        cursor.execute("SELECT * FROM agent_events WHERE task_id = ? ORDER BY id ASC", (task['id'],))
        task['events'] = [dict(r) for r in cursor.fetchall()]
        return json.dumps({'status': 'success', 'task': task}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def clear_agent_traces(confirm: bool = False) -> str:
    """Delete all agent traces. Requires confirm=True."""
    if not confirm:
        return json.dumps({'status': 'error', 'message': 'Confirmation required. Set confirm=True to clear.'}, ensure_ascii=False)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agent_events")
        cursor.execute("DELETE FROM agent_tasks")
        conn.commit()
        return json.dumps({'status': 'success', 'message': 'All traces cleared'}, ensure_ascii=False)
    finally:
        conn.close()


# ============================================================
# Batch Evaluation Tool
# ============================================================


@mcp.tool()
def batch_evaluate_jds(jds: str) -> str:
    """Evaluate multiple JDs at once. Accepts JSON array of objects with jd_text and company_name fields.
    Example: [{"jd_text": "招聘嵌入式工程师...", "company_name": "CompanyA"}, {"jd_text": "招聘Python开发...", "company_name": "CompanyB"}]"""
    import uuid
    try:
        items = json.loads(jds) if isinstance(jds, str) else jds
    except (json.JSONDecodeError, TypeError):
        return json.dumps({'status': 'error', 'message': 'Invalid JSON input'}, ensure_ascii=False)
    if not isinstance(items, list):
        return json.dumps({'status': 'error', 'message': 'Input must be a JSON array'}, ensure_ascii=False)

    results = []
    for item in items:
        jd_text = item.get('jd_text', '')
        company_name = item.get('company_name', '')
        task_id = f"batch-{uuid.uuid4().hex[:8]}"

        conn = get_db_connection()
        try:
            profile_content = ""
            if os.path.exists(PROFILE_PATH):
                with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                    profile_content = f.read().lower()

            score, highlights, risks, positive_matches, negative_matches, rejection_warnings = _evaluate_jd_inner(
                conn, jd_text, profile_content
            )

            final_score = min(max(score, 0), 100)
            reason = f"最终评估得分 {final_score} 分。亮点: {'; '.join(highlights) or '综合符合基准要求'}。"
            if risks:
                reason += f" 风险提示: {'; '.join(risks)}。"

            result_payload = {
                'task_id': task_id,
                'company_name': company_name,
                'match_score': final_score,
                'highlights': highlights,
                'risks': risks,
                'positive_matches': positive_matches,
                'negative_matches': negative_matches,
                'rejection_warnings': rejection_warnings,
                'reason': reason
            }
            record_agent_trace(task_id=task_id, agent_name="JD-Evaluator", event_type="evaluation_result", payload=result_payload, status="completed")
            results.append({'status': 'success', 'result': result_payload})
        except Exception as e:
            results.append({'status': 'error', 'company_name': company_name, 'message': str(e)})
        finally:
            conn.close()

    return json.dumps({'status': 'success', 'count': len(results), 'results': results}, ensure_ascii=False)


# ============================================================
# System Notification Tool
# ============================================================


@mcp.tool()
def notify_db_changed() -> str:
    """Notify the dashboard UI that the database has changed (triggers SSE refresh)."""
    try:
        from routes.dashboard import notify_db_changed as _notify
        _notify()
        return json.dumps({'status': 'success', 'message': 'UI notified'}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)}, ensure_ascii=False)
