# AGENTS.md

## Project Overview
- **System**: JHTracker — 本地 AI 智能求职求贤追踪与推荐平台。
- **Architecture**:
  - **Backend**: FastAPI + FastMCP (`backend/src/main.py` + `backend/src/mcp_server.py`), Python 3.10+, SQLite (aiosqlite + FTS5).
  - **Frontend**: React 18 SPA (Vite + TypeScript + Tailwind CSS + Lucide React), `frontend/src/`.
- **Private Data Isolation**:
  - Public job data: `data/public_jobs.db` (repo-level).
  - Private user data: `~/.JHTracker/user_data.db` (resumes, applications, HITL feature weights).
  - Directory cleanup rules: `build/` can be rebuilt at any time; `fig/` and `data/` contain important resources (handle with care).

## Developer Commands

### Backend (`backend/`)
- **Run Tests (Crucial)**:
  - Default `pytest` will fail with `ModuleNotFoundError: No module named 'src'`.
  - Always run with python module mode:
    ```bash
    # Run all tests
    python -m pytest
    
    # Run a single test file or test function
    python -m pytest tests/test_recommendations.py
    python -m pytest tests/test_recommendations.py::test_recommendation_and_hitl_loop -v
    ```
- **Dev Servers**:
  - Web API server: `python src/main.py` (runs FastAPI on `http://127.0.0.1:8000`)
  - FastMCP server: `python src/mcp_server.py`

### Frontend (`frontend/`)
- **Dev Server**: `npm run dev` (Vite dev server on `http://localhost:5173`)
- **Typecheck & Build**: `npm run build` (`tsc && vite build`)
- **Preview**: `npm run preview`

### Full-Stack Quickstart
- Windows cmd: `.\scripts\start.bat`
- Windows PowerShell: `.\scripts\start.ps1`

### Quality Gate & Verification (Lightweight)
- **统一自测入口（必跑）**:
  - 在完成功能、修复 Bug 或向用户汇报“已完成”前，**必须**运行极速自测：
    ```bash
    python scripts/check_all.py
    ```
    *(默认 5 秒内完成：后端 pytest 41+ 测试 + 前端 tsc 类型校验 + 版本一致性)*
  - 准备发版或完整打包验证时才运行全量模式：
    ```bash
    python scripts/check_all.py --full
    ```
- **质量防线底线（Quality Baseline）**:
  - 严禁擅自删除既有测试用例以“掩盖报错”；测试用例总数只许增加或持平，严禁产生新增失败。
- **更新日志**:
  - 单人日常开发无需额外流程；正式打 tag 发版时可通过 `changelog.d/` 配合 `compile_changelog.py` 归档。

### Version Management
- **Single Source of Truth (SSOT)**: 根目录 `VERSION` 文件（SemVer: `MAJOR.MINOR.PATCH`，当前为 `0.1.0`）。
- **Bump Version**:
  ```bash
  python scripts/bump_version.py check          # 检查前后端版本一致性
  python scripts/bump_version.py patch          # 修订版本 (0.1.0 -> 0.1.1)
  python scripts/bump_version.py minor          # 次版本 (0.1.0 -> 0.2.0)
  python scripts/bump_version.py major          # 主版本 (0.1.0 -> 1.0.0)
  python scripts/bump_version.py set 0.2.1      # 指定版本
  ```

## Key Architecture & Data Quirks
- **Database Schema**:
  - `public_jobs.db`: `jobs` table + `jobs_fts` (SQLite FTS5 virtual table for full-text search).
  - `~/.JHTracker/user_data.db`: `resumes`, `applications`, `hitl_weights`, `interaction_logs`.
- **Recommendation & HITL Feedback**:
  - `RecommendationService` scores jobs against active resume skills & tags.
  - Action `ACCEPT`: increases feature weights, records interaction, and automatically creates an `ApplicationItem` with status `PENDING_APPLY`.
  - Action `REJECT`: suppresses feature weights down to a minimum decay floor (0.05), dampens related industry weights, and hides job from future recommendations.
- **FastMCP Tools**:
  - Defined in `backend/src/mcp_server.py`: `job_search`, `job_recommend`, `job_feedback`, `resume_optimize`, `job_sync_run` (trigger spider sync into public DB), `job_get_detail` (fetch full JD and application links), `job_add_external` (safely upsert discovered jobs with deduplication hash).
- **Agent Skills**:
  - `skills/job-sourcing/SKILL.md`: Comprehensive skill for intelligent domestic job scraping, long-tail campus network recruitment sourcing, and deduplicated external job ingestion.
  - `skills/job-advisor/SKILL.md`: Dedicated career advisor skill for deep resume/thesis profiling, domain-gated multi-channel retrieval, strict frequency capping (applied company exclusion + max 3 pending jobs per company), and FastMCP direct agent push.

## Agent Conventions
- **Language**: Default communication language is **Chinese** (中文).
- **Communication Style**: Direct and concise; avoid conversational filler or repetitive preambles/postambles.
- **Verification Workflow**:
  - Backend changes: verify with `python -m pytest`.
  - Frontend changes: verify with `npm run build` (runs `tsc` and `vite build`).
