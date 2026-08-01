## Context

JHTracker is a local-first Flask application. We want to modernize the UI/UX without abandoning Flask/Jinja2 or introducing complex Node.js build pipelines (npm, Vite, Tailwind CLI). We retain Bootstrap 5 as the CSS framework foundation and layer on custom CSS design tokens inspired by shadcn/ui and Linear. We also integrate HTMX and Alpine.js via vendorized static JS files for server-rendered reactive UI.

See proposal.md and specs for details.

## Goals / Non-Goals

**Goals:**
- Zero-build pipeline (no npm, no Node build steps). All JS/CSS vendor assets stored locally under `static/vendor/`.
- Modern Zinc dark design language using CSS variables.
- Server-rendered HTML fragments using HTMX (`hx-get`, `hx-trigger="every 15s"`).
- Reorganized 5-domain navigation sidebar + AI Daily Briefing card on Dashboard.
- Skill match badges (`C++ ✓`, `ROS ✓`, `外包 ✗`) on cards.

**Non-Goals:**
- No SPA framework rewrite (React, Vue, Next.js).
- No changes to underlying database schema or ORM models.
- No cloud dependencies or external CDN requirements.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| CSS Framework | Bootstrap 5 + Custom CSS Tokens | Preserves existing layout structure while upgrading visual tokens to Zinc dark theme (#09090b canvas, #18181b cards, #27272a 1px borders) |
| Dynamic UI Paradigm | HTMX + Jinja2 Partials | Server returns rendered Jinja2 HTML partials (`_decision_inbox.html`, `_agent_tasks.html`), replacing complex hand-written JS string concatenation |
| Interactive State | Alpine.js (vendorized ~15KB) | Light client-side reactive state for modal visibility and accordion expansion without full JS framework overhead |
| Navigation Architecture | 5 Domain Groups | Reorganizes sidebar links from DB-centric tables to Workflow-centric Domains: Workspace, Opportunities, Applications, Agent Center, Knowledge Base |

## Risks / Trade-offs

- [HTMX Fallback] If HTMX fails to load or JavaScript is disabled, fallback to standard page refreshes. -> Native Jinja2 forms ensure full usability.
- [CSS Overrides] Bootstrap 5 defaults may collide with custom Zinc variables. -> Override at `:root` and `.card`/`.nav-link` level cleanly.

## Open Questions

None.