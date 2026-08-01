## Why

Agent Task Center 中的任务卡片右侧按钮「查看 Trace Log」与事件数徽章排版错位，在 4 列侧栏中参差不齐。公司详情页 (`company_detail.html`) 信息量少、视觉效果平淡，缺少 AI 评分高亮展示、匹配分析标签（技能亮点与风险预警）以及投递记录的简历版本关联信息。

## What Changes

- **Agent Task Center 双行紧凑卡片**：将 `templates/_agent_tasks.html` 中任务卡片重构为两行布局（上行：Agent名 + 事件数，下行：Task ID + 对齐的 Trace Log 链接），确保右侧按钮绝对对齐不偏移。
- **公司档案页重构**：`templates/company_detail.html` 整体视觉升级：
  - 顶部 AI 评分大徽章与匹配度展示
  - AI 匹配诊断区（亮点 `ROS ✓` / `C++ ✓` 与风险 `外包 ✗` 标签）
  - 左侧 `col-md-4` 公司元数据卡片视觉增强
  - 右侧 `col-md-8` 投递记录卡片增加关联简历版本名展示

## Capabilities

### New Capabilities
- `company-detail-enhancement`: 公司详情页 360° 升级，含 AI 评分高亮、匹配标签、简历版本关联展示

### Modified Capabilities
- `htmx-jinja-partials`: `_agent_tasks.html` 任务卡片布局从单行挤列改为双行紧凑对齐格式

## Impact

- `templates/_agent_tasks.html` — 双行紧凑卡片布局，修复按钮对齐
- `templates/company_detail.html` — 重构全页布局与视觉层级
- `tests/test_agent_api.py` — 更新 HTML 端点测试以匹配新模板