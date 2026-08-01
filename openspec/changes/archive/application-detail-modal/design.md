## Context

See `proposal.md`. 当前 `applications.html` 每张卡片内联显示所有信息，公司名链接跳转到 `/companies/<id>`，面试评价表单 `_feedback_form.html` 内联在每张卡片底部。Bootstrap 5 已 vendor 化，原生支持 Modal 组件。

## Goals / Non-Goals

**Goals:**
- 公司名点击改为触发 Bootstrap Modal
- Modal 内展示完整投递详情：公司信息、AI 评分、简历版本、反馈、面试评价、Offer 管理
- 面试评价表单从卡片内联移入 modal
- 卡片列表本身保持不变

**Non-Goals:**
- 不新增 API 端点 — 所有数据已通过模板上下文传递
- 不修改后端路由

## Decisions

- **Bootstrap Modal 原生实现**：Bootstrap 5 已 vendor 化，直接用 `data-bs-toggle="modal"` + `data-bs-target="#appDetailModal{{ a.id }}"`，无需额外 JS
- **每个卡片一个 modal**：在 for 循环内为每个 application 生成一个带唯一 ID 的 modal 模板，`data-bs-target` 精准匹配
- **Modal 内公司名链接**：保留 `<a href="/companies/{{ a.company.id }}">` 跳转功能，用户想深入了解公司时可直接点击跳转
- **Modal 布局**：顶部公司名+岗位+状态 → 渠道/薪资/截止/JD 链接 → AI 评分+简历版本 → 反馈 → 面试评价

## Risks / Trade-offs

- [Modal 数量] 每张卡片一个 modal 会增加 DOM 节点数，但列表分页最多 30 条，Bootstrap 可正常处理
- [表单提交后] 面试评价表单提交后页面会刷新重定向，modal 会关闭 → 可接受，当前其他表单也是同样行为