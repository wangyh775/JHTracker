## 1. Dashboard Layout Restructuring

- [x] 1.1 In `templates/dashboard.html`, refactor the main layout row to use `col-lg-8` (Left Analytics) and `col-lg-4` (Right Agent Panel)
- [x] 1.2 Move AI Daily Briefing, Stats Cards, Funnel, Charts, and Scatter Plot into the left `col-lg-8` column
- [x] 1.3 Move Decision Inbox, Agent Task Center, Upcoming Timeline, and Recent Activity into the right `col-lg-4` column

## 2. Micro-Card & Scroll Container Styling

- [x] 2.1 Add scroll container styles for Decision Inbox (`max-height: 380px; overflow-y: auto;`) and Agent Task Center (`max-height: 260px; overflow-y: auto;`) in `templates/dashboard.html`
- [x] 2.2 Update `templates/_decision_inbox.html` layout for compact vertical display inside 4-column sidebar

## 3. Documentation Update

- [x] 3.1 Update `docs/hitl-feedback-loop.md` to reflect the new split grid Dashboard layout and right-column Agent Co-Pilot panel

## 4. Verification

- [x] 4.1 Run pytest test suite to ensure all 79 unit tests pass without regressions