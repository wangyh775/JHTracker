## Context

In `templates/dashboard.html`, Decision Inbox and Agent Task Center are placed sequentially at the bottom of the page in 12-column full-width cards. This forces users to scroll several viewports down to perform HITL approvals. We re-architect the page grid layout into a split layout using Bootstrap 5 grid classes (`col-lg-8` and `col-lg-4`).

See proposal.md and specs for motivation and behavior contracts.

## Goals / Non-Goals

**Goals:**
- Move Decision Inbox and Agent Task Center to the top right of the viewport (`col-lg-4`).
- Maintain left 8-column layout (`col-lg-8`) for AI Daily Briefing, Stats Cards, Funnel, Charts, and Scatter Plot.
- Add max-height scroll containers for right-column panels (`max-height: 380px` for Inbox, `max-height: 260px` for Tasks).
- Ensure full responsive stacking on mobile (`col-12`).

**Non-Goals:**
- No backend logic or route changes.
- No database model changes.
- No changes to HTMX or SSE endpoints.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Grid Architecture | `col-lg-8` (Left) + `col-lg-4` (Right) | Aligns with modern AI Copilot / IDE workspace layouts (e.g. GitHub, Notion AI) |
| Vertical Inbox Cards | Micro-card format in `_decision_inbox.html` | Fits neatly into 4-column width with vertical button layout and badges |
| Scroll Containers | `max-height: 380px; overflow-y: auto;` | Prevents right column from expanding endlessly while allowing full scroll access |

## Risks / Trade-offs

- [Narrow Width] In `col-lg-4`, recommendation cards have less horizontal space. -> Mitigated by stacking Approve/Reject buttons vertically or in compact flex wrap.

## Open Questions

None.