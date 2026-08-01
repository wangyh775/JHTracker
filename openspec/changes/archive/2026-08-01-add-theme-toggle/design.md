## Context

See `proposal.md`. 当前 `base.html` 硬编码 `data-bs-theme="dark"`，自定义 Zinc CSS 变量在 `:root` 中仅定义暗色值。Bootstrap 5.3 支持 `[data-bs-theme="dark"]` 和 `[data-bs-theme="light"]` 选择器覆盖。Alpine.js 已 vendor 化 (`static/vendor/js/alpine.min.js`) 但未使用。

## Goals / Non-Goals

**Goals:**
- 定义一套 Zinc 亮色 CSS 变量（`[data-bs-theme="light"]` 作用域）
- 在侧栏底部添加主题切换按钮（☀️/🌙 图标切换）
- 用 Alpine.js 实现 `data-bs-theme` 切换 + localStorage 持久化
- 亮色模式下所有 Bootstrap 组件（card、form、modal、table 等）自动适配

**Non-Goals:**
- 不修改 Bootstrap vendor CSS
- 不新增 JS 依赖

## Decisions

- **Alpine.js 实现切换逻辑**：Alpine 已 vendor 化，用 `x-data` + `x-model` 绑定 `data-bs-theme`，比纯 JS 更简洁且与现有架构一致
- **亮色变量映射**：暗色 `#09090b` → 亮色 `#ffffff`，`#18181b` → `#f4f4f5`，`#27272a` → `#e4e4e7`，`#f4f4f5` → `#09090b`，`#a1a1aa` → `#52525b`，`#71717a` → `#a1a1aa`
- **按钮位置**：侧栏底部用户信息下方，`<hr>` 分隔后放置

## Risks / Trade-offs

- [亮色遗漏] 部分模板可能硬编码了 `bg-dark`/`text-light` 类 → Bootstrap 5.3 的 `data-bs-theme` 会自动处理大多数场景，少量硬编码需手动检查
- [FOUC] 页面加载时可能出现闪白 → 在 `<head>` 中内联一个 `<script>` 优先读取 localStorage 设置 `data-bs-theme`，避免 Alpine 初始化延迟