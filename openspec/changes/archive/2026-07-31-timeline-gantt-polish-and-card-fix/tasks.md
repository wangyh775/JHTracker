## 1. 投递记录 HTML 结构修复

- [x] 1.1 在 `templates/applications.html` 中补齐 `<div class="card mb-2">` 缺失的闭合 `</div>` 标签，解决嵌套堆叠 Bug

## 2. 时间线甘特图美化与动态过滤

- [x] 2.1 在 `templates/timeline.html` 顶部增加控制开关（`[ ] 显示已完成` / `[ ] 显示已过期`）
- [x] 2.2 重构 `templates/timeline.html` 的 JS `render()` 方法，默认过滤已完成及已过期节点，动态关联控制开关
- [x] 2.3 升级节点列表为微卡片 (Micro-Cards) 样式，美化甘特图柱体配色与悬浮框 (Tooltip)

## 3. 验证

- [x] 3.1 运行测试套件 (`pytest tests/`) 确认无逻辑回归
- [ ] 3.2 启动应用验证卡片不再堆叠且时间线过滤功能正常