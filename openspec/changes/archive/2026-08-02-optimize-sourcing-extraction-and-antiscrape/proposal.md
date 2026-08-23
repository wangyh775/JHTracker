## Why

Agent 自动检索企业岗位时，抓取到的原始招聘页面包含大量无关信息（导航栏、福利宣传、推荐职位列表），Token 浪费率高达 90%，且噪音干扰匹配打分的准确性。同时，国内招聘平台（BOSS 直聘、猎聘、国聘等）反爬机制严格，且容易搜到过期陈旧页面或非目标招聘类型/毕业届数的岗位。

## What Changes

- **方向 C：结构化数据提取与 Token 瘦身**：在 Skill SOP 中新增 JD 结构化清洗规范，提取关键技术栈（Must-have）、薪资范围（标准化为 k/月）、工作地点，丢弃福利宣传等无关内容，将 JD Payload 从 3000+ Tokens 压缩至 200~400 Tokens。
- **招聘类型偏好与届数/时间硬拦截 Gate**：
  - 在 `data/profile.md` 支持 `recruitment_type` 配置（`校招` / `社招` / `不限`）。若未配置，Agent 主动询问并回写。
  - 当为 `校招` 时，强制要求目标届数为 2027 届校招（2026.09-2027.08 毕业窗口）且发布时间晚于 2026 年 7 月 1 日；当为 `社招` 时放宽届数约束但保持发布时间与工作经验匹配校验。
- **方向 D：反爬与平台降级矩阵**：针对 BOSS 直聘、猎聘、国聘/官网三类平台，分别制定 XHR 拦截、Firecrawl Stealth、搜索引擎快照的阶梯降级策略，并增加优雅降级输出规范。

## Capabilities

### New Capabilities
- `sourcing-optimization`: 企业检索 Skill 优化——JD 结构化数据提取与 Token 瘦身规范、招聘类型（校招/社招）偏好读取、毕业届数/发布时间硬拦截门，以及面向国内招聘平台的反爬降级矩阵。

### Modified Capabilities
（无）

## Impact

- **`data/profile.md` / `skills/candidate-profile-and-resume/SKILL.md`**：增加 `recruitment_type` 字段的读取与写入支持。
- **`skills/job-sourcing-and-scoring/SKILL.md`**：新增招聘类型判断、JD 结构化提取、届数/时效拦截 Gate 与反爬降级矩阵，重构现有 5 层检索协议的落地方案。
- **测试**：新增招聘类型解析、薪资提取、届数/时效拦截、结构化清洗、降级抓取场景的模拟测试用例。