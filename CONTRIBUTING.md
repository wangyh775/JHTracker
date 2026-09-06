# 贡献指南 (Contributing to JHTracker)

感谢您关注并有意向为 **JHTracker** 贡献代码！JHTracker 致力于为全球开发者和求职者打造一个完全私密、透明且高度智能的本地求职推荐与追踪平台。

通过遵守以下指南，您可以帮助我们保持高质量的代码库与良好的社区协作氛围。

---

## 🚀 快速上手 (Quickstart)

### 1. 克隆与分支规范
- 请将本仓库 Fork 到您的个人 GitHub 账户下。
- 克隆您的 Fork 并创建特性分支：
  ```bash
  git clone https://github.com/<your-username>/JHTracker.git
  cd JHTracker
  git checkout -b feat/your-feature-name
  # 或者修复类分支
  git checkout -b fix/issue-description
  ```

### 2. 本地开发环境准备
- **Python**: 3.10+
- **Node.js**: 18+ (推荐 20+)

```bash
# 启动前后端（或使用一键脚本）
.\scripts\start.ps1
```

---

## 🛠️ 开发与贡献规范

### 1. 架构与数据隔离红线 (Architecture Rules)
- **严格遵循双库物理隔离**：
  - 公共岗位库：`data/public_jobs.db`。由爬虫统一写入，仅存储全网公开岗位元数据。
  - 用户私有库：`~/.JHTracker/user_data.db`。任何用户简历、申请记录、HITL 权重、个性化交互，**绝对不能**写入项目根目录下的公共库，也**绝对禁止**加入任何中心化遥测代码。
- **FastMCP 工具规范**：
  - 所有新增的 MCP 智能体工具必须在 `backend/src/mcp_server.py` 中规范声明，定义强类型 Pydantic Schema，并添加 `@audit_mcp_tool` 审计装饰器。

### 2. 代码风格 (Code Style)
- **后端 (Python)**:
  - 遵循 PEP 8 规范，类型注解（Type Hints）全覆盖。
  - 使用异步 I/O（`aiosqlite`, `httpx`），杜绝在主循环中使用阻塞型同步调用。
- **前端 (TypeScript / React)**:
  - 严格 TypeScript 模式，禁止使用 `any`。
  - 界面风格保持既有的 **Cyber-Dark**（深色科技感、高信息密度）设计系统，优先使用 Tailwind CSS。

---

## 🧪 必须通过的验证流程 (Pre-commit Verification)

在提交 PR 之前，您必须在本地运行并通过所有测试与编译检查：

### 1. 后端单元测试
```bash
cd backend
python -m pytest
```
> 所有测试用例必须 100% 通过。如新增了核心模块，请在 `backend/tests/` 补充对应的单元测试。

### 2. 前端类型检查与打包构建
```bash
cd frontend
npm run build
```
> 必须保证 `tsc` 类型检查零错误，`vite build` 产物构建无报错。

---

## 📝 提交信息规范 (Commit Convention)

推荐遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
- `feat`: 新增特性（例如新增特定平台的招聘爬虫、优化推荐算法特征）
- `fix`: 修复缺陷
- `docs`: 文档变更
- `style`: 样式调整（不影响代码逻辑）
- `refactor`: 重构代码
- `test`: 新增或修改测试用例
- `chore`: 构建过程或辅助工具的变动

---

## 📬 提交流程 (Pull Request Checklist)

1. 确认已更新相关文档（若涉及新 API 或配置项）。
2. 确保 PR 描述详尽，包含修改背景、测试步骤与预期效果。
3. 关联对应的 Issue（例如 `Fixes #12`）。
4. 提交 PR 后，GitHub Actions CI 将自动运行自动化测试与编译构建。
