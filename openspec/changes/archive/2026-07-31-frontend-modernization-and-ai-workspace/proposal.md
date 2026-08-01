## Why

JHTracker 目前的前端页面视觉较为粗糙，信息架构按数据库表罗列，且动态区域依赖手写 JS 拼接 HTML 字符串。为了将 JHTracker 从传统的 CRUD 管理工具升级为现代化的 **Human-in-the-Loop AI 求职工作台**，需要在保持零构建（Flask + Jinja2 + 双击启动）的前提下，对视觉系统、数据交互模式、信息架构和卡片组件进行渐进式现代化升级。

## What Changes

- **Phase 1 (视觉系统)**：引入 shadcn/Linear 风格的 Zinc 锌黑设计语言 (CSS Variables)，重构 `base.html` 基础卡片、精细边框 (1px border)、徽章与字阶阶梯。
- **Phase 2 (架构升级)**：引入本地静态文件 HTMX + Alpine.js，使用 Jinja2 局部模板 (`_partial.html`) 替换 JS `innerHTML` 拼接字符串逻辑。
- **Phase 3 (工作台导航与 AI 简报)**：重构侧边栏架构为 5 大工作区（工作台、机会库、投递跟踪、Agent 中心、知识库）， Dashboard 增加 AI Daily Briefing（每日智能简报 + 优先处理提案卡片）。
- **Phase 4 (富文本数据卡片)**：重构公司和岗位列表，从死板表格升级为包含技能契合度标签 (`ROS ✓`, `C++ ✓`, `外包 ✗`) 的 Rich Cards。

## Capabilities

### New Capabilities
- `zinc-design-system`: 基于 CSS 变量的深色 Zinc 锌黑设计系统，包含卡片、徽章、字阶、玻璃拟态与精细边框
- `htmx-jinja-partials`: HTMX + Alpine.js 局部模板驱动机制，服务端返回 HTML 替换手写 JS innerHTML
- `ai-workspace-navigation`: 5 大求职工作区架构与 Dashboard AI Daily Briefing 每日智能简报
- `rich-opportunity-cards`: 包含技能匹配分析 (`ROS ✓`, `C++ ✓`, `外包 ✗`) 的富文本岗位与公司卡片

### Modified Capabilities
<!-- No existing spec requirements are changing -->

## Impact

- `templates/base.html` — 全局 CSS 变量与设计系统样式更新
- `templates/_sidebar.html` — 导航重构为 5 大工作区
- `templates/dashboard.html` — Dashboard 引入 AI Daily Briefing 简报区，并抽离 HTMX 局部模板
- `templates/_decision_inbox.html` — 新增 Jinja2 局部模板
- `templates/_agent_tasks.html` — 新增 Jinja2 局部模板
- `static/vendor/js/htmx.min.js` — 本地新增 HTMX 静态文件
- `static/vendor/js/alpine.min.js` — 本地新增 Alpine.js 静态文件
- `routes/agent_api.py` — 新增返回 Jinja2 局部模板的 HTML 路由端点
- `routes/dashboard.py` — 扩展 AI Daily Briefing 数据源逻辑