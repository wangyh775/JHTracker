## 1. 招聘类型偏好读取与 profile.md 支持

- [x] 1.1 在 `skills/candidate-profile-and-resume/SKILL.md` 与 `skills/job-sourcing-and-scoring/SKILL.md` Step 0 中增加 `recruitment_type`（`校招` / `社招` / `不限`）偏好字段的读取与缺失主动询问回写逻辑。

## 2. 结构化数据提取与 Token 瘦身 SOP 规范

- [x] 2.1 在 `skills/job-sourcing-and-scoring/SKILL.md` 的 Step 2 之后新增 Step 2d "JD 结构化提取与 Token 瘦身规范"，定义 Must-have、Nice-to-have、薪资、地点、招聘类型、毕业届数、发布时间等提取字段及丢弃噪音规范。
- [x] 2.2 在 `skills/job-sourcing-and-scoring/SKILL.md` 中增加薪资标准化解析示例表，涵盖 "20-35K·16薪"、"25k-40k"、"40-70万/年" 等常见中文格式并换算为 k/月。

## 3. 毕业届数与时间时效硬拦截 Gate

- [x] 3.1 在 `skills/job-sourcing-and-scoring/SKILL.md` 中新增 Step 2e "毕业届数与发布时间硬拦截 Gate"，在 `recruitment_type: 校招` 时要求岗位发布日期 > 2026-07-01 且目标届数为 2027 届校招（或 2026.09-2027.08 毕业窗口），凡不符合的岗位直接 SKIP 淘汰。
- [x] 3.2 在 Step 2e 中增加关键词对照表（"2027届校招"、"2027毕业生" 为通过；"2026届"、"社招"、"3年以上经验" 为拦截）。

## 4. 平台专有反爬避让与 4 阶降级矩阵

- [x] 4.1 重构 `skills/job-sourcing-and-scoring/SKILL.md` 的 Step 1 检索协议，为 BOSS直聘、猎聘、国聘/官网增加平台专属的 4 阶降级策略（Stage 1 API/XHR 拦截 → Stage 2 Stealth Proxy → Stage 3 快照缓存 → Stage 4 优雅降级）。
- [x] 4.2 补充 Stage 4 优雅降级规范，要求 Agent 在拦截阻断时输出真实可验证链接提示人类手动辅助，严格禁止伪造岗位数据。

## 5. 测试与验证

- [x] 5.1 编写/更新单元测试，验证招聘类型读取、薪资转换逻辑、届数与时效拦截、结构化清洗格式兼容性。
- [x] 5.2 运行全量 `pytest` 测试套件，确保现有测试全部通过。