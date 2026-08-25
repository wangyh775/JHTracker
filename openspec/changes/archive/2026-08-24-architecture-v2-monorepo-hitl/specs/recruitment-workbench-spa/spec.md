## Purpose

Provides a modern, responsive Single Page Application (SPA) recruitment workbench delivering Kanban lifecycle management, side-by-side floating clipboards for manual form assistance, and real-time execution feedback.

## ADDED Requirements

### Requirement: Interactive Kanban Pipeline Management
The system SHALL present job applications across structured recruitment stages (待投递, 已投递, 笔试/测评, 技术一面, 技术二面, HR/终面, Offer, 已挂/归档) with drag-and-drop or one-click status transitions.

#### Scenario: Advancing application stage
- **WHEN** user moves a job card from "待投递" to "已投递"
- **THEN** system updates the application status in backend SQLite and records the application timestamp

### Requirement: Side-by-Side Floating Quick-Copy Drawer
The system SHALL provide a persistent floating drawer displaying candidate profile blocks (education, 3-track projects, publications, awards, self-evaluation) with one-click copy to clipboard.

#### Scenario: Copying project description to clipboard
- **WHEN** user clicks on a project entry in the floating drawer
- **THEN** system copies the exact formatted project bullet points to the system clipboard and displays a visual toast confirmation

### Requirement: One-Click CDP Autofill Trigger and Live SSE Progress
The system SHALL provide an immediate action button to initiate browser autofill via backend CDP and stream real-time execution milestones to the UI.

#### Scenario: Triggering and viewing live autofill progress
- **WHEN** user clicks "⚡ 预填当前页面" on a job detail view
- **THEN** system invokes the backend autofill endpoint and displays real-time progress steps (connecting Chrome, uploading resume, filled N fields) via Server-Sent Events

### Requirement: Multi-Track Resume and Script Switcher
The system SHALL allow users to toggle between Mechanical, Automation, and General resume tracks and dynamically inspect matching cover letter greetings.

#### Scenario: Switching track on a job item
- **WHEN** user toggles resume version to "自动化版"
- **THEN** system selects `resumes/王云鹤_简历_自动化.pdf`, updates the default greeting text with MPC/STM32 keywords, and updates recommendation metadata
