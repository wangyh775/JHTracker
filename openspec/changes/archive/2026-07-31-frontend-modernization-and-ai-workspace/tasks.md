## 1. Phase 1: Zinc Design System & Base Styling

- [x] 1.1 Update `templates/base.html` CSS variables for Zinc dark design tokens (`#09090b` canvas, `#18181b` cards, `#27272a` 1px borders, `#f4f4f5` text, `#6366f1` indigo accent)
- [x] 1.2 Upgrade card, badge, button, and table border styling across `templates/base.html` for 1px crisp borders and subtle hover glassmorphism

## 2. Phase 2: HTMX & Alpine.js Integration

- [x] 2.1 Download/vendorize `htmx.min.js` into `static/vendor/js/htmx.min.js` and `alpine.min.js` into `static/vendor/js/alpine.min.js`
- [x] 2.2 Include `htmx.min.js` and `alpine.min.js` script tags in `templates/base.html`
- [x] 2.3 Create Jinja2 partial template `templates/_decision_inbox.html` for Decision Inbox proposals
- [x] 2.4 Create Jinja2 partial template `templates/_agent_tasks.html` for Agent Task Center items
- [x] 2.5 Add HTML partial route endpoints `/api/agent/decisions/pending-html` and `/api/agent/tasks-html` in `routes/agent_api.py`
- [x] 2.6 Refactor `templates/dashboard.html` to use HTMX `hx-get` and `hx-trigger="load, every 15s"` instead of hand-written JS string concatenation

## 3. Phase 3: AI Workspace Navigation & Dashboard AI Briefing

- [x] 3.1 Reorganize `templates/_sidebar.html` into 5 Workflow Domains: Workspace (工作台), Opportunities (机会库), Applications (投递跟踪), Agent Center (智能体中心), Knowledge Base (知识库)
- [x] 3.2 Add AI Daily Briefing card component on `templates/dashboard.html` showing stale application follow-up alerts and pending approval proposals
- [x] 3.3 Update `routes/dashboard.py` to calculate AI Briefing summary data (unanswered applications >7 days, high-match pending approvals)

## 4. Phase 4: Rich Opportunity & Application Cards

- [x] 4.1 Create Jinja2 partial/macro for Rich Opportunity Cards in `templates/companies.html` and `templates/applications.html`
- [x] 4.2 Add skill match breakdown badges (`ROS ✓`, `C++ ✓`) and risk warnings (`外包 ✗`) on opportunity cards

## 5. Verification & Tests

- [x] 5.1 Add unit tests in `tests/test_agent_api.py` for `/api/agent/decisions/pending-html` and `/api/agent/tasks-html`
- [x] 5.2 Verify all existing 77 pytest cases pass