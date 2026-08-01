## 1. 亮色 CSS 变量

- [x] 1.1 在 `base.html` 的 `<style>` 中新增 `[data-bs-theme="light"]` 作用域的 Zinc 亮色 CSS 变量

## 2. 主题切换按钮

- [x] 2.1 在 `_sidebar.html` 底部用户信息后添加主题切换按钮（☀️/🌙 Alpine.js 绑定）
- [x] 2.2 在 `base.html` 的 `<head>` 中添加 FOUC 防护脚本（优先读取 localStorage 设置 `data-bs-theme`）

## 3. 验证

- [x] 3.1 运行测试确认无回归
- [x] 3.2 启动应用，手动切换亮/暗主题确认渲染正常