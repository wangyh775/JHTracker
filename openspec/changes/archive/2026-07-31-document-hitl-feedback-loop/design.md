## Context

This is a pure documentation change — no code changes, no schema changes, no behavior changes. The codebase already implements the full HITL feedback loop (DecisionFeedback/Memory models, decision API endpoints, Decision Inbox UI, evaluate_jd feedback ingestion, agent trace logging). The `docs/` directory is out of sync with the actual codebase.

See proposal.md for motivation. The existing docs files at `docs/database.md`, `docs/api.md`, `docs/SKILLS_AND_MCP_GUIDE.md`, and `docs/README.md` are the starting point.

## Goals / Non-Goals

**Goals:**
- `docs/database.md` accurately reflects all 10 models (currently shows 8)
- `docs/api.md` lists all 15 agent API endpoints (currently shows 8)
- `docs/SKILLS_AND_MCP_GUIDE.md` lists all 9 MCP tools (currently shows 6)
- New `docs/hitl-feedback-loop.md` describes the complete HITL closed loop
- `docs/README.md` index links to the new HITL doc

**Non-Goals:**
- No code changes to models, routes, templates, or MCP tools
- No changes to `openspec/specs/` main specs (this is a doc-only change)
- No changes to `docs/development.md`, `docs/ai-scoring.md`, `docs/getting-started.md`, `docs/feature-archive.md`, `docs/architecture.md` (they are already accurate)

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| New vs patch | Both | database.md/api.md/SKILLS_GUIDE are patches; HITL closed loop is a new document because it spans multiple layers and no single existing doc fits |
| HITL doc format | Same as existing docs (Chinese markdown + Mermaid) | Consistency with existing docs/ style |
| Source of truth | Codebase (models.py, routes/agent_api.py, mcp_server.py, templates/dashboard.html) | Docs must reflect what's actually implemented, not what was planned |
| Skip specs | `.openspec.yaml: skip_specs: true` | No behavior changes — pure documentation |

## Risks / Trade-offs

- [Staleness] Documentation is a snapshot — may drift again. Mitigation: add a "last updated" date to each doc (already standard in existing docs)
- [Oversight] Codebase may have changed in ways not captured by this audit. Mitigation: re-read relevant source files before writing each doc section

## Open Questions

None.