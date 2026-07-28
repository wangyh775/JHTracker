# 贡献指南

欢迎为 JHTracker 贡献代码！以下是一些基本规范。

## 开发环境搭建

```bash
git clone <repo-url>
cd career-tracker
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-ai.txt  # 可选，开发 AI 功能时需要

# 启用调试模式
set FLASK_DEBUG=1   # Windows
export FLASK_DEBUG=1  # macOS / Linux
python app.py
```

## 代码规范

- Python 代码遵循 PEP 8
- 函数和类有 docstring
- 新增功能尽量补单元测试（`tests/` 目录）
- 提交信息使用中文，格式：`<类型>: <描述>`
  - 类型：feat / fix / docs / refactor / chore / test

## 提交 PR

1. Fork 仓库并创建特性分支：`git checkout -b feature/your-feature`
2. 提交改动：`git commit -m "feat: 添加 xxx 功能"`
3. 推送分支：`git push origin feature/your-feature`
4. 在 GitHub 上发起 Pull Request，描述清楚改动内容

## 报告 Bug

请使用 GitHub Issues，并包含：
- 复现步骤
- 期望行为 vs 实际行为
- 操作系统 + Python 版本
- 浏览器控制台报错截图（如果是前端问题）

## 目录结构

```
career-tracker/
├── app.py              # 应用入口
├── config.py           # 配置
├── models.py           # 数据模型
├── routes/             # 路由蓝图
├── templates/          # Jinja2 模板
├── scripts/            # 命令行工具
├── prompts/            # AI 提示词模板
├── career_data/        # 公司清单数据源（用户可编辑）
└── data/               # 运行时数据（gitignore）
```
