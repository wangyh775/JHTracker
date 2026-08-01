## 1. Modal 模板

- [x] 1.1 在 `applications.html` 的 for 循环内为每个 application 添加 Bootstrap Modal 模板，包含唯一 ID `appDetailModal{{ a.id }}`
- [x] 1.2 Modal 内展示：公司名（可跳转链接）、岗位、状态徽章、渠道、薪资、截止日期、JD 链接、AI 评分 + Agent 分析、简历版本名
- [x] 1.3 Modal 内展示反馈/进度文本区域，以及 Offer 状态管理（当 status=Offer 时）

## 2. 公司名改为 Modal 触发

- [x] 2.1 将第 103 行公司名 `<a href="/companies/...">` 改为 `data-bs-toggle="modal" data-bs-target="#appDetailModal{{ a.id }}"` 触发按钮

## 3. 面试评价移入 Modal

- [x] 3.1 从卡片底部移除 `{% include '_feedback_form.html' with context %}`
- [x] 3.2 在 Modal 内添加 `{% include '_feedback_form.html' with context %}`

## 4. 验证

- [x] 4.1 运行测试确认无回归
- [ ] 4.2 启动应用，点击公司名确认 modal 弹出且内容完整