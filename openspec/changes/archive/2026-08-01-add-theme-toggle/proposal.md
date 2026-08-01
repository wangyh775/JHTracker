## Why

当前系统仅支持暗色主题（Zinc Dark），用户无法切换亮色模式。Bootstrap 5.3 原生支持双主题切换，但缺少切换按钮和亮色 CSS 变量定义。

## What Changes

- 在 `templates/base.html` 中新增一套 Zinc 亮色 CSS 变量（`[data-bs-theme="light"]`）
- 在 `templates/_sidebar.html` 底部新增一个主题切换按钮（🌙/☀️ 图标切换）
- 使用 Alpine.js 实现 `data-bs-theme` 属性切换 + localStorage 持久化

## Capabilities

### New Capabilities
- `theme-toggle`: 支持用户在亮色/暗色主题间切换，偏好存储在 localStorage 中

### Modified Capabilities
- `zinc-design-system`: 新增亮色主题 CSS 变量定义，现有暗色变量保持不变

## Impact

- `templates/base.html` — 新增 `[data-bs-theme="light"]` CSS 变量覆盖
- `templates/_sidebar.html` — 底部新增主题切换按钮
- `openspec/specs/zinc-design-system/spec.md` — 更新 spec 以反映双主题支持