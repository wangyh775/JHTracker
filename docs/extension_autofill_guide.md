# Hermes 智能网申助手浏览器插件使用与集成指南

## 1. 概述
Hermes 智能网申助手是 Career-Tracker 1.0 (Flask) 的伴随式浏览器扩展（WebExtension Manifest V3）。它将本地知识库（`profile.md`）、4轨简历库（控制算法、自动化与嵌入式、机电电气、机械仿真）与 AnswerBank 开放题生成能力，无缝注入到任意企业网申官网（如北森 Beisen、Moka、智联、牛客等）。

## 2. 插件安装与加载步骤 (Chrome / Edge)
1. 打开 Chrome 或 Edge 浏览器，访问扩展管理页面：
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
2. 在右上角开启 **开发者模式 (Developer Mode)**。
3. 点击 **加载已解压的扩展程序 (Load unpacked)**。
4. 选择本项目根目录下的 `extension/` 文件夹。
5. 确认扩展列表中出现 **Hermes 智能网申助手** 且状态为启用。

## 3. 核心功能与工作流 (场景 B: 审批直达)

```
[1.0 看板 Decision Inbox / 待投递清单]
                 │
                 ▼ 点击 [⚡ 一键直达智能网申] (携带 #hermes_app_id=xx)
[浏览器打开招聘官网页面]
                 │
                 ▼ 插件自动连接本地 Flask (localhost:5000) 加载画像与 4 轨简历
[页面右下角点亮 🟢 悬浮球]
                 │
                 ├── 1. 自动分步感知 (Step Wizard Perception)：每点一步自动扫描表单
                 ├── 2. 拟人打字机注入 (Anti-Cheat Typing)：高斯击键扰动 + 标点停顿
                 ├── 3. 4 轨动态换轨 (Track Switcher)：在浮窗中随时切换不同方向简历
                 ├── 4. 显式挂载简历 (CDP File Attachment)：一键通过 CDP 注入本地 PDF
                 │
                 ▼
[人类在页面底端亲自点击 "提交申请"] (Zero-Submit HITL)
                 │
                 ▼ 状态自动同步回 tracker.db (status='已投递')
```

## 4. 后端 API 清单 (Flask 1.0)
- `GET /api/agent/applications/<id>/autofill-payload`：获取指定岗位的画像映射、4轨简历文件路径与开放题生成结果。
- `POST /api/agent/applications/match-by-url`：根据当前 Tab URL 自动反查匹配的活跃岗位记录。
- `POST /api/agent/applications/<id>/sync-submitted`：网申提交后，自动更新数据库投递状态为“已投递”并记录投递凭证。
