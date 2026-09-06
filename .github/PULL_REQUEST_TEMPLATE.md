## 描述 (Description)
<!-- 请简要阐述此 PR 解决的问题或引入的新功能 -->

## 关联 Issue (Related Issue)
<!-- 如果有关联的 issue，请在此链接，例如 Fixes #123 -->
Fixes #

## 变更类型 (Type of Change)
- [ ] 🐛 Bug 修复 (Bug fix)
- [ ] ✨ 新功能 (New feature)
- [ ] 🕷️ 新增或更新招聘平台爬虫 (New or updated spider adapter)
- [ ] 📝 文档更新 (Documentation update)
- [ ] 🎨 代码格式或前端样式优化 (Style / UI tweak)
- [ ] ♻️ 代码重构与架构改进 (Refactoring)
- [ ] 🧪 测试用例补充 (Tests)

## 验证与检查清单 (Checklist)
- [ ] 本地已运行 `cd backend && python -m pytest`，所有测试用例 100% 通过。
- [ ] 本地已运行 `cd frontend && npm run build`，类型检查与构建无报错。
- [ ] 代码遵循双库物理隔离架构，未引入任何外部遥测或泄露用户私有库数据。
- [ ] 如涉及 MCP 工具变动，已在 `backend/src/mcp_server.py` 更新 Schema 与审计装饰器。
