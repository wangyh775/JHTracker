## Context

Pure documentation update. No code changes. MCP expanded from 9 to 36 tools, HITL closed loop implemented, but 4 documentation files are stale. Design philosophy (Agent-First, Human-in-the-Loop, Data Sovereignty) has never been written down anywhere.

See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- `docs/api.md` MCP tools list updated from 9 to 36, organized by domain
- `docs/README.md` (documentation index) adds design philosophy section
- Root `README.md` updated with 36 tools, design philosophy, updated architecture diagram
- `docs/architecture.md` design decisions table adds 3 new entries

**Non-Goals:**
- No code changes to any files
- No changes to `docs/database.md`, `docs/development.md`, `docs/ai-scoring.md`, `docs/getting-started.md`, `docs/feature-archive.md`, `docs/hitl-feedback-loop.md`, `docs/SKILLS_AND_MCP_GUIDE.md` (already up to date)

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Design philosophy location | Root README.md + docs/README.md + docs/architecture.md | Root README is the entry point for new users; docs/README is the index; architecture.md is where design decisions belong |
| Three principles | Agent-First, Human-in-the-Loop, Data Sovereignty | Covers all current design choices without overlap |
| MCP tool list format | Grouped by 11 domains with headers | 36 tools as flat list is unreadable; domain grouping makes it skimmable |

## Risks / Trade-offs

- [Staleness] Documentation will drift again. → Mitigated by the "last updated" date already present in each doc