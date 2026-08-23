## Context

See proposal.md for motivation.

In `templates/timeline.html`:
1. `rangeFor` currently sets `xmin` for `month` view to `new Date(y, m, now.getDate(), 0, 0, 0)` (today's midnight). Any node starting earlier in the month (e.g. 1st of the current month, or previous days) gets cropped out on the left side of Chart.js time scale.
2. `renderCardList` attaches `onclick="openTimelineModal(item.id, ..., '${item.description}')"` directly to card HTML strings. Unescaped quotes or newlines in descriptions cause Javascript `SyntaxError` which breaks card rendering and Chart initialization.

## Goals / Non-Goals

**Goals:**
- Fix `xmin` and `xmax` range calculation in `renderGantt()` for `month` and `quarter` view ranges so that events earlier in the month are visible (e.g., setting month view range to cover the full current month or from start of month to end of month / +30 days).
- Standardize modal opening by storing item index or ID in `data-id` / `data-index` attributes on the micro-cards or using an in-memory lookup function instead of embedding inline JS function calls with unescaped strings.

**Non-Goals:**
- Modifying backend timeline endpoints or database schemas.

## Decisions

- **Decision 1: Dynamic Date Range Padding for Gantt Charts**
  - For `month` view, set `xmin` to the 1st of the current month (or min of current items and 1st of month) and `xmax` to the end of the month / +30 days from 1st of month, ensuring nodes starting earlier in the current month remain visible.
  - For `quarter` view, start `xmin` from 1 month prior to current date or start of quarter.

- **Decision 2: Safe Micro-Card Click Binding via In-Memory Item Array**
  - In `renderCardList`, render `data-index="${idx}"` or `data-id="${item.id}"` on the micro-card element.
  - Attach click event listeners via JavaScript delegation or query selector mapping into the existing global `items` / `filtered` array, calling `openTimelineModal` with clean properties from the object rather than inline JS string literals.

## Risks / Trade-offs

- [Risk] If `filtered` array index shifts upon filtering, looking up by index might be stale.
  - Mitigation: Look up item by `item.id` from `items` array using `items.find(i => i.id === id)`.
