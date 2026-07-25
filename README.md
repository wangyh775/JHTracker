# Job Hunt Tracker

自动化工程师/机电工程师求职全流程管理工具。

## 功能

- **公司清单管理**：500+家公司，按行业/城市/匹配度筛选
- **投递跟踪**：状态流转（待投递→已投递→笔试→面试→Offer/拒绝）
- **面试复习手册**：内置8科目复习资料 + 编程题集
- **看板统计**：投递漏斗、转化率、城市分布、行业分布
- **时间线**：秋招/春招节点提醒
- **目标公司**：S/A/B/C 优先级分级管理

## 技术栈

- Backend: Flask (Python)
- Frontend: Bootstrap 5 + Chart.js + vanilla JS
- DB: SQLite
- 数据导入: 从 career/ 目录的 Markdown 清单批量导入

## 启动

```bash
cd career-tracker
pip install -r requirements.txt
python app.py
# 打开 http://localhost:5000
```
