## 1. Fix Gantt Date Range (xmin/xmax)

- [x] 1.1 In `templates/timeline.html`, update `renderGantt()` month view: set `xmin` to `new Date(y, m, 1)` (1st of current month) instead of `new Date(y, m, now.getDate())` (today)
- [x] 1.2 Keep `xmax` as `new Date(y, m, now.getDate() + 30)` or adjust to `new Date(y, m+1, 0)` (end of month) + pad to cover events
- [x] 1.3 Verify quarter view: set `xmin` to `new Date(y, m-1, now.getDate())` (1 month back) or `new Date(y, m-2, 1)` (start of quarter) to capture items beginning before today

## 2. Replace Inline `onclick` with Safe Event Delegation

- [x] 2.1 In `renderCardList()`, replace inline `onclick="openTimelineModal(...)"` with `data-id="${item.id}"` attribute on the card `<div>` element
- [x] 2.2 Remove the inline `onclick` string interpolation from the template literal
- [x] 2.3 Add a delegated click listener that reads `item.id` from `data-id`, looks up the item in the global `items` array, and calls `openTimelineModal(item.id, item.start, item.end, item.type, item.title, item.description, item.done)`
- [x] 2.4 Remove the dead `document.querySelectorAll('.timeline-item')` event binding block (lines 369-381) that is never triggered since the cards use `.timeline-card` class