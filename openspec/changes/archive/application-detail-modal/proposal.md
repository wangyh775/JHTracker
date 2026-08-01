## Why

投递记录列表中点击公司名会跳转到公司档案页，用户需要返回才能继续查看其他投递，操作路径长。同时面试评价表单内联在每张卡片底部，导致列表过长。

## What Changes

- 公司名链接改为触发 Bootstrap Modal，modal 内展示完整投递详情（公司信息、AI 评分、简历版本、反馈、面试评价、Offer 管理）
- modal 内公司名保留跳转到公司档案页的链接
- 面试评价表单（`_feedback_form.html`）从卡片内联移入 modal 中

## Capabilities

### New Capabilities
- `application-detail-modal`: 投递记录列表支持点击公司名弹出详情 Modal，内联展示所有投递相关信息

## Impact

- `templates/applications.html` — 公司名改为 modal 触发，新增 modal 模板，移除内联 `_feedback_form.html`
- `templates/_feedback_form.html` — 保留不变，但不再内联在卡片底部，仅由 modal 引用