## 1. Agent Task Center Dual-Row Layout

- [x] 1.1 Read current `_agent_tasks.html` to understand existing card structure
- [x] 1.2 Refactor each task card to dual-row layout: row 1 = agent name + event count badge, row 2 = task ID + aligned Trace Log link
- [x] 1.3 Verify button alignment at `col-lg-4` width in browser DevTools

## 2. Company Detail 360° Upgrade

- [x] 2.1 Read current `company_detail.html` to understand existing structure and data context
- [x] 2.2 Add AI score hero badge at top of page with color-coded styling (green/yellow/red)
- [x] 2.3 Add match analysis tag row: skill highlights (ROS ✓) as green badges, risk warnings (外包 ✗) as red badges
- [x] 2.4 Enhance left `col-md-4` company metadata card with improved visual hierarchy
- [x] 2.5 Enhance right `col-md-8` application records to display associated resume version name

## 3. Verify

- [x] 3.1 Run existing tests (`pytest tests/`) to confirm no regressions
- [x] 3.2 Launch app with `start.bat` and visually confirm both pages render correctly  <!-- Confirmed by user -->