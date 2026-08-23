## Why

Timeline (Gantt chart) items are currently failing to display properly or throwing JavaScript runtime errors on `templates/timeline.html`.
First, the Chart.js x-axis minimum date (`xmin`) is anchored strictly at `now.getDate()` in month and quarter views, clipping out any events that start prior to today (e.g. earlier in the month) or cross over from past dates.
Second, passing multi-line `description` strings directly into inline `onclick="openTimelineModal(...)"` HTML attributes causes JS syntax errors (`Uncaught SyntaxError: Invalid or unexpected token`), halting execution and preventing micro-cards and Gantt charts from rendering.

## What Changes

- Fix Gantt chart date range calculations (`xmin` and `xmax`) so that events starting earlier in the current month or quarter remain visible on the timeline.
- Refactor timeline micro-card modal triggers to avoid inline JS string escaping issues (e.g., using `data-*` attributes and event delegation instead of inline `onclick="..."` string templates with unescaped newline risks).
- Ensure filtering and toggling for completed/expired items functions smoothly without JS syntax exceptions.

## Capabilities

### Modified Capabilities

- `timeline-gantt`: Adjust view range calculations and safe modal event binding for timeline items.

## Impact

- `templates/timeline.html`: Frontend HTML/JS layout for timeline rendering and modal triggers.
- `routes/timeline.py`: Backend timeline data endpoint if serialization formats need enhancement.
