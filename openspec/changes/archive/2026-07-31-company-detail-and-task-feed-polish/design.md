## Context

See `proposal.md` for motivation. Current state: `_agent_tasks.html` uses a single-row flex layout that causes button misalignment when the sidebar narrows to `col-lg-4`. `company_detail.html` displays company metadata and application records in a plain stacked layout without AI score prominence, skill match tags, or resume version linkage.

## Goals / Non-Goals

**Goals:**
- Fix Agent Task Center card button alignment in narrow sidebar via dual-row compact layout
- Upgrade company detail page with AI score badge, skill match / risk tags, richer metadata card, and resume version links in application records
- Maintain existing HTMX partial rendering pattern (`_agent_tasks.html` already served via `/api/agent/tasks-html`)

**Non-Goals:**
- No API changes — all new data is already served by existing endpoints
- No routing changes — company detail remains at `/company/<int:company_id>`
- No database schema changes

## Decisions

- **Dual-row card layout over flexbox fix**: A single-row flexbox with overflow control would still crowd content in a 4-col sidebar. Dual-row layout (row 1: agent name + event count badge; row 2: task ID + Trace Log link) guarantees each card has consistent height and the button occupies the right edge of the second row every time.
- **CSS utility classes over custom CSS**: Use existing Bootstrap 5 + Zinc utility classes (`.d-flex`, `.justify-content-between`, `.gap-2`, `.text-muted`, `.badge`) to avoid adding new stylesheets.
- **Company detail layout**: Use `col-md-4` / `col-md-8` split with AI score badge as a hero element at the top, followed by a match analysis tag row, then the metadata card on the left and application records on the right.

## Risks / Trade-offs

- [Layout regression] Dual-row may look sparse in wider viewports → Add responsive classes so the card stays compact across all breakpoints.
- [Data staleness] AI score and match tags are computed at JD submission time → Mitigation: display the evaluation timestamp alongside the score.