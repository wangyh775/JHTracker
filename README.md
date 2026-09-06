<div align="center">

```ascii
       __  __  ___________________  ___   ________ __ __________ 
      / / / / /_  __/ __ \/   |  / ____/  / //_/ ____// __ \      
 __  / /_/ /_  / / / /_/ / /| | / /      / ,< / __/  / /_/ /      
/ /_/ / __  / / / / _, _/ ___ |/ /___   / /| / /___ / _, _/       
\____/_/ /_/ /_/ /_/ |_/_/  |_|\____/  /_/ |/_____//_/ |_|        
```

### High-Performance Local-First Intelligent Job Hunting & Recruitment Platform

<p align="center">
  <a href="docs/README_ZH.md"><img src="https://img.shields.io/badge/Language-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-blue.svg?style=for-the-badge" alt="简体中文" /></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Language-English-indigo.svg?style=for-the-badge" alt="English" /></a>
  <a href="https://github.com/wangyh775/JHTracker/releases"><img src="https://img.shields.io/badge/Version-v0.1.1_Genesis-cyan.svg?style=for-the-badge&logo=git&logoColor=white" alt="Release Version" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge" alt="MIT License" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI_Python3.10+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/Frontend-React_18_TypeScript-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black" alt="React 18" /></a>
</p>

<!-- Cockpit Hero Banner Preview -->
<p align="center">
  <img src="docs/diagrams/hero-banner.svg" alt="JHTracker Cockpit Preview" width="100%" />
</p>

</div>

---

## ⚡ The 3-Second Hook: Numbers That Matter

<div align="center">

| 🏢 **24,180 Real JDs** | 🔒 **100% Private Vault** | ⚡ **&lt;50ms Full-Text Search** | 🤖 **10 FastMCP Tools** |
| :---: | :---: | :---: | :---: |
| Full offline campus database ready on first boot with zero scraping lag. | Physical dual-DB isolation (`~/.JHTracker/user_data.db`). Never touches clouds. | SQLite FTS5 inverted index with instant column-pinned AG Grid rendering. | Native agent protocol for Claude Desktop, Cursor, and OpenCode CLI. |

</div>

```
Traditional Boards:  ❌ Scattered Links ──> ❌ SaaS Sells Resumes ──> ❌ Black-Box Feeds ──> ❌ Manual Copy Hell
JHTracker Standard:  ✅ 24k AG-Grid  ──> ✅ ~/.JHTracker Vault ──> ✅ HITL Energy Loop ──> ✅ 1-Click FastMCP Push
```

---

## 🎯 5-Second Zero-Config Taste

Experience instant job intelligence on 24,000+ positions right now — **zero API keys, zero cloud registration, zero telemetry**:

```bash
# Query the local SQLite FTS5 engine for top AI & Backend positions
curl -s "http://127.0.0.1:8000/api/jobs/search?q=Python+FastAPI&limit=2" | jq .
```

```json
{
  "total": 348,
  "items": [
    {
      "id": "job_ali_cloud_902",
      "company": "阿里云计算",
      "title": "后端研发专家 (AI Agent 方向)",
      "salary": "28k-45k · 16薪",
      "city": "杭州",
      "degree": "硕士及以上",
      "apply_url": "https://talent.alibaba.com/campus/position-detail?lang=zh&positionId=...",
      "skills": ["Python", "FastAPI", "FastMCP", "SQLite", "Distributed Systems"]
    }
  ],
  "latency_ms": 32.4
}
```

---

## 💥 Why JHTracker? (Stop the Daily Frustration)

<p align="center">
  <img src="docs/diagrams/why-pain-fix.svg" alt="Why JHTracker — Pain vs Fix" width="100%" />
</p>

---

## 🥊 Hardcore Matrix: What Sets JHTracker Apart?

| Capability Dimension | ⚡ **JHTracker** | 🏢 Commercial Platforms (Boss/Nowcoder/LinkedIn) | 📋 Notion / Excel Templates | 🐍 DIY Custom Scrapers |
| :--- | :--- | :--- | :--- | :--- |
| **Privacy & Security** | **100% Physical Dual-DB Isolation** (`~/.JHTracker/user_data.db` air-gapped) | ⚠️ Centralized cloud custody: Profile & credentials hosted on third-party SaaS | ⚠️ Cloud-hosted workspace; susceptible to shared team visibility | ⚠️ Plain-text local files without encryption or process isolation |
| **Out-of-the-Box Data** | **24,000+ Curated Campus Postings** included in repo | ⚠️ Platform-locked: Fragmented across different silos; requires multiple accounts | ❌ Zero initial data: Requires 100% manual entry row-by-row | ⚠️ Fragile against anti-scraping updates & dynamic web changes |
| **Recommendation Engine** | **Dual-Recall HITL Adaptive Loop** (Transparent feedback & decay) | ⚠️ Commercial feed priorities: Opaque platform ranking algorithms | ❌ None (Static spreadsheets cannot compute feature weights) | ❌ Simple text filter without continuous learning feedback |
| **Lifecycle Kanban** | **6-Stage High-Density Board** (120px cards, interview retros, credentials) | ⚠️ Fragmented conversations; difficult to maintain unified cross-platform status | ⚠️ Performance degradation on large sheets; manual status toggling | ❌ None (Terminal outputs or raw tabular rows only) |
| **AI Agent Integration** | **FastMCP Standard Protocol** (10 audited tools for Claude / Cursor / OpenCode) | ❌ Walled garden: No standard protocol for personal local LLM orchestration | ⚠️ Requires external paid automation services (Zapier/Make) | ⚠️ Ad-hoc CLI scripts lacking standardized JSON-RPC schemas |
| **ATS Resume Diagnosis** | **Precision Keyword Radar** (Read-only master protects core resume assets) | ⚠️ Broad suggestions; rarely provides transparent JD-skill differential diffs | ❌ None | ❌ None |
| **Telemetry & Offline** | **Zero Telemetry, Zero Analytics, 100% Offline Capable** | ⚠️ Online dependent: Continuous session analytics & behavioral telemetry | ⚠️ Cloud connectivity required for real-time synchronization | ⚠️ Network dependent on target servers and proxies |

---

## 🧠 Flagship Deep Dive: Human-in-the-Loop (HITL) Adaptive Engine

Commercial recruitment recommendation algorithms are notorious black boxes designed to maximize platform advertising revenue, repeatedly resurfacing irrelevant jobs you have dismissed.

JHTracker flips the paradigm: **You own the model weights, and your decisions train your private local matrix in real time.**

<p align="center">
  <img src="docs/diagrams/hitl-loop.svg" alt="HITL Adaptive Loop & Dual Recall Architecture" width="100%" />
</p>

### Mathematical Formulation of Dynamic Hybrid Scoring

For any candidate position $J$ and user profile $U$:

$$\text{FinalScore}(J, U) = 0.50 \cdot S_{\text{skill}}(J, U) + 0.30 \cdot S_{\text{hitl}}(J, W) + 0.20 \cdot S_{\text{freshness}}(J)$$

1. **Dual-Channel Recall**:
   - **Branch A (Targeted Recall)**: Runs SQLite FTS5 inverted search over JD requirements using hard skills extracted from the active resume.
   - **Branch B (Discovery Recall)**: Fetches the latest verified 24-hour job releases to discover emerging opportunities.
2. **Dynamic Weight Reinforcement & Decay**:
   - **ACCEPT Action**: Category, industry, and city weights associated with position $J$ are boosted by **$+15\%$** in `~/.JHTracker/user_data.db`. The job is automatically converted into an application record with status `PENDING_APPLY`.
   - **REJECT Action**: Associated feature weights decay exponentially ($\times 0.70$). A **hard safety floor of $0.05$** ensures related disciplines are not permanently silenced, while the specific rejected position is permanently hidden from future recommendations.
3. **Anti-Flood Capping**:
   - Enforces a strict maximum of **3 pending jobs per enterprise** to prevent large conglomerates from flooding recommendation feeds.
   - Discards candidates with fit scores below $0.40$.

---

## 🔒 Security Architecture: Physical Dual-DB Isolation

<p align="center">
  <img src="docs/diagrams/architecture-flow.svg" alt="Physical Dual-DB Architecture & Agent Scheduling Topology" width="100%" />
</p>

| Database Repository | Physical Location | Git Visibility | Read/Write Policy | Contains |
| :--- | :--- | :--- | :--- | :--- |
| **Public Jobs Repository** | `data/public_jobs.db` | Trackable in Git | Read-Only to Agents; Append-Only via Spider Dedup | 24,000+ jobs, SQLite FTS5 index, external ingested postings |
| **User Private Vault** | `~/.JHTracker/user_data.db` | **Air-gapped from Git** | Isolated User OS Home; Sandboxed Access | Master resume, 6-stage applications, HITL weights, interview retros |

---

## 🤖 Agent-Native in Action: FastMCP Protocol

JHTracker exposes an industrial-grade **FastMCP** (Model Context Protocol) server over `stdio` and `JSON-RPC`, allowing local AI assistants to autonomously query, recommend, and track applications without exposing user data to the cloud.

### 10 Audited FastMCP Tools

1. `job_search(query, city, limit)`: High-performance SQLite FTS5 full-text search.
2. `job_recommend(top_k, min_score)`: Dual-recall HITL personalized recommendation stream.
3. `job_feedback(job_id, action, feedback_reason)`: Human decision feedback (`ACCEPT` / `REJECT`).
4. `job_agent_push(job_id, recommend_reason, match_score, agent_name)`: Direct push high-matching positions with deduplication and frequency capping.
5. `job_get_detail(job_id)`: Fetches complete job description, requirements, and official direct application URLs.
6. `resume_get_profile()`: Safely reads the parsed active user profile (skills, degree, target locations).
7. `resume_optimize(job_id)`: Analyzes JD-resume keyword gaps and generates tailored resume drafts.
8. `resume_update_keywords_matrix(skills, target_roles)`: Incrementally synchronizes updated skills and keyword matrices into HITL features.
9. `job_add_external(...)`: Ingests jobs discovered from university portals or forum networks with SHA-256 / MD5 deduplication.
10. `job_sync_run(spider_name)`: Triggers background multi-channel recruitment crawler sync (supports `qiuzhifangzhou`, `wondercv`, `nowcoder`).

### Client Configuration

Replace `<PROJECT_ROOT>` with the absolute path to your cloned repository (e.g. `/path/to/JHTracker` or `C:\\path\\to\\JHTracker`).

#### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "jhtracker": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "<PROJECT_ROOT>/backend"
    }
  }
}
```

#### OpenCode CLI / Cursor (`opencode.json`)
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "jhtracker": {
      "type": "local",
      "command": ["python", "-m", "src.mcp_server"],
      "cwd": "<PROJECT_ROOT>/backend"
    }
  }
}
```

### Live Agent Terminal Slice

```
User ▶ "Analyze my active resume profile and recommend 2 top matching backend positions that I haven't applied to yet."

Agent ⚡ Calling tool: jhtracker.job_recommend(top_k=2, min_score=0.75)
Agent ──> Tool Result:
[
  {
    "job_id": "ali_cloud_902",
    "company": "阿里云计算",
    "title": "后端研发专家 (AI Agent 方向)",
    "score": 0.92,
    "matched_skills": ["Python", "FastAPI", "SQLite", "FTS5", "React"],
    "missing_skills": ["K8s Operators"],
    "apply_url": "https://talent.alibaba.com/campus/position-detail?..."
  },
  {
    "job_id": "bytedance_rec_401",
    "company": "字节跳动",
    "title": "分布式系统研发工程师 (校招)",
    "score": 0.88,
    "matched_skills": ["Python", "AsyncIO", "Distributed Cache", "Git"],
    "missing_skills": ["Raft Consensus"],
    "apply_url": "https://jobs.bytedance.com/campus/position/..."
  }
]

Agent ▶ "Based on your technical profile (Python/FastAPI/FastMCP/React), I found 2 high-affinity positions:
1. 阿里云计算 — 后端研发专家 (AI Agent 方向) | Match Score: 92%
   • Key Strengths: Your FastAPI & FastMCP toolkit aligns directly with their core agent infrastructure.
   • Gap to Bridge: Familiarize yourself with K8s Operator development prior to the interview.
   • Direct Portal: https://talent.alibaba.com/...
2. 字节跳动 — 分布式系统研发工程师 | Match Score: 88%
   • Key Strengths: Strong async I/O foundation and SQLite storage optimization.
Would you like me to tailor a targeted resume draft for Alibaba Cloud?"
```

---

## 🚀 Quick Start

### Prerequisites
- **Python**: `3.10+`
- **Node.js**: `18+` (npm 9+)

### Windows 1-Click Launch (Recommended)

```powershell
# In PowerShell:
.\scripts\start.ps1

# Or in Windows CMD:
.\scripts\start.bat
```

The script automatically activates the Python virtual environment, starts the FastAPI backend on `http://127.0.0.1:8000`, and serves the Vite frontend on `http://localhost:5173`.

### Manual Step-by-Step Launch

```bash
# 1. Setup Backend
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python src/main.py

# 2. Setup Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** in your browser to enter the Cyber-Dark Cockpit.

---

## 🧪 Quality Verification & Testing Gate

Run the full automated test suite and production build check before submitting changes:

```bash
# Backend verification: 43 comprehensive pytest suites
cd backend
python -m pytest

# Frontend verification: TypeScript strict typing & Vite production build
cd frontend
npm run build
```

---

## 🗺️ Release Roadmap

- [x] **v0.1.1 Genesis (Current Baseline)**:
  - 24,000+ offline campus job database with SQLite FTS5 full-text indexing.
  - Cyber-Dark UI cockpit featuring AG Grid v36 virtualization with pinned company columns and decoupled salary/degree metrics.
  - 6-stage high-density application tracking Kanban board with interview retrospective notes and compact cards.
  - Multi-version resume workbench with full-syntax Markdown rendering, skill tag highlighting, and instant persistence.
  - Multi-engine AI resume optimizer supporting user-configured OpenAI-compatible APIs (`custom_api`), local CLI agents (`opencode`, `hermes`), and rule-based fallback (`builtin`).
  - FastMCP server exposing 10 audited tools for local AI agent orchestration.
  - Physical dual-DB architecture isolating user data in `~/.JHTracker/user_data.db`.

---

## 📚 Complete Documentation Suite

For in-depth architecture, data schemas, and API guides, explore the official documentation:

- 📖 **[3-Minute Quickstart Guide](docs/quickstart.md)**
- 📘 **[End-to-End User Manual](docs/user-guide.md)**
- 🏛️ **[System Architecture & Math Specification](docs/architecture.md)**
- 🔒 **[Data Storage & Physical Privacy Isolation Standard](docs/data-storage-and-privacy.md)**
- 🔌 **[RESTful API Reference Manual](docs/api-reference.md)**
- 🤖 **[FastMCP Agent Integration Guide](docs/mcp-agent-guide.md)**
- 🛠️ **[Developer Environment & Contributing Guide](docs/developer-guide.md)**
- 🕷️ **[Spider Development & Ingestion Pipeline](docs/spider-development.md)**

---

## 📄 License & Privacy Manifesto

JHTracker is released under the **[MIT License](LICENSE)**.

**Privacy Manifesto**:
1. Your resumes, applications, interview notes, and behavioral weights belong strictly to you and remain on your local filesystem (`~/.JHTracker/user_data.db`).
2. JHTracker contains zero telemetry, zero behavioral tracking, and zero cloud analytics.
3. AI agents interact strictly through audited, local FastMCP tools with explicit sandboxing.
