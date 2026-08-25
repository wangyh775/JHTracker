## 1. Backend REST API Feature Parity Expansion

- [x] 1.1 Implement `/api/v1/dashboard/briefing` endpoint returning AI Daily Briefing, stale application warnings (>7 days), and urgent deadline countdowns
- [x] 1.2 Implement `/api/v1/traces` endpoint with pagination and filtering for agent trace auditing
- [x] 1.3 Implement `/api/v1/answer-bank` endpoint returning categorized real-project technical Q&As
- [x] 1.4 Implement `/api/v1/compare/offers` calculation endpoint for net compensation, tax, and 12% housing fund projections

## 2. Vue 3 Views Implementation (Full Feature Parity)

- [x] 2.1 Implement `DashboardView.vue` with AI Briefing cards, stale application alarms, and recruitment pipeline KPI cards
- [x] 2.2 Implement `CompaniesView.vue` with Tier S/A/B/C filters, city/industry tag searching, and modal company editor
- [x] 2.3 Implement `OfferCompareView.vue` with multi-offer comparison matrix and housing fund mortgage calculation charts
- [x] 2.4 Implement `DecisionInboxView.vue` with HITL approval queue for agent-discovered proposals (Approve to 待投递 / Reject)
- [x] 2.5 Implement `AnswerBankView.vue` with categorized technical defense Q&As (MPC/EKF, Fluent CFD, EPLAN, HyperMesh) and live search
- [x] 2.6 Implement `TracesView.vue` with chronological agent action trees and JSON payload inspector
- [x] 2.7 Implement `ProfileView.vue` with SSOT profile editing and 3-track resume PDF switcher (Mechanical / Automation / General)

## 3. Navigation & Floating Toolkit Integration

- [x] 3.1 Update `App.vue` sidebar to integrate all 7 primary feature views and active tab persistence
- [x] 3.2 Enhance `QuickCopyDrawer.vue` to support one-click copying for all profile sections (education, 3-track projects, publications, awards, self-evaluation)
- [x] 3.3 Wire global CDP Autofill trigger button with toast feedback and Zero-Submit safety indicators

## 4. End-to-End Verification & Build

- [x] 4.1 Run backend pytest suite verifying new REST API endpoints
- [x] 4.2 Run `pnpm run build` to compile the full-featured SPA into `backend/app/static/dist`
- [x] 4.3 Verify full interactive workflow across all 7 views in the browser
