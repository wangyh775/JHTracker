"""JHTracker MCP Server — Exposes career memory resources and tools for AI agents via Model Context Protocol."""
import os
import json
import sqlite3
from mcp.server.fastmcp import FastMCP

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
    source_url: str = None
) -> str:
    """Create a new job application record under specified company with default '待投递' (pending) status and HITL recommendation metadata."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM companies WHERE id = ?", (company_id,))
        comp = cursor.fetchone()
        if not comp:
            return json.dumps({'status': 'error', 'message': 'Company not found'}, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO applications (company_id, position, status, channel, job_desc, url, match_score, agent_reason, agent_task_id, source_url, created_at, updated_at)
            VALUES (?, ?, '待投递', ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (company_id, position, channel, job_desc, url, match_score, agent_reason, agent_task_id, source_url))
        conn.commit()
        app_id = cursor.lastrowid
        return json.dumps({
            'status': 'success',
            'application': {
                'id': app_id,
                'company_id': company_id,
                'company_name': comp['name'],
                'position': position,
                'status': '待投递',
                'url': url,
                'match_score': match_score,
                'agent_reason': agent_reason,
                'agent_task_id': agent_task_id,
                'source_url': source_url
            }
        }, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def get_user_preferences() -> str:
    """Get candidate career profile, negative constraint rules (excluded tech/companies), and recent human rejection notes."""
    conn = get_db_connection()
    try:
        profile_content = ""
        if os.path.exists(PROFILE_PATH):
            with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
                profile_content = f.read()

        cursor = conn.cursor()
        cursor.execute("SELECT category, rule_value, raw_feedback FROM memories ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()

        negative_rules = []
        recent_rejection_notes = []

        for row in rows:
            if row['rule_value']:
                negative_rules.append({
                    'category': row['category'],
                    'rule_value': row['rule_value']
                })
            if row['raw_feedback']:
                recent_rejection_notes.append(row['raw_feedback'])

        return json.dumps({
            'status': 'success',
            'profile': profile_content,
            'negative_rules': negative_rules,
            'recent_rejection_notes': recent_rejection_notes[:20]
        }, ensure_ascii=False)
    finally:
        conn.close()


if __name__ == '__main__':
    mcp.run()
