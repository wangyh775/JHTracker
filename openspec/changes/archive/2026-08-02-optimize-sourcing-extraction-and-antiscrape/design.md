## Context

当前 `job-sourcing-and-scoring` Skill 的 Step 0 仅读取 `enterprise_preference`（企业偏好），缺少 `recruitment_type`（校招/社招/不限）偏好字段的读取与路由。Step 2 之后缺少结构化提取、招聘类型判断、届数/时间硬拦截步骤。同时，Step 1 缺少针对国内招聘平台的专有避让策略。

## Goals / Non-Goals

**Goals:**
- 在 `data/profile.md` 中支持 `recruitment_type` 字段，读取缺失时 Agent 主动询问并回写。
- 在 Skill SOP 中新增 JD 结构化提取步骤（Step 2.d），提取 Must-have Skills、薪资、地点、招聘类型、毕业届数、发布时间。
- 根据 `recruitment_type` 实施不同的硬拦截 Gate：
  - `校招`：限定 2027 届校招（2026.09 - 2027.08 毕业窗口），且发布时间 > 2026-07-01。
  - `社招`：放宽届数约束，但校验工作经验与发布的匹配度。
- 薪资字符串标准化规则，统一转换为 k/月。
- 为 BOSS直聘、猎聘、国聘/官网三类平台新增 4 阶降级矩阵。

**Non-Goals:**
- 不修改后端数据库结构或 REST API 端点。
- 不引入新的外部依赖或 MCP 工具。
- 不改变 evaluate_jd 底层算法。

## Decisions

### 1. `recruitment_type` 沿用 `enterprise_preference` 的读取模式
- **选择**: 在 Skill Step 0 中与 `enterprise_preference` 一起读取，缺失时提示用户选择并回写 `data/profile.md`。
- **替代方案**: 在 profile.md 中写死只能由用户手动编辑。理由：Agent 主动询问更适合新用户初次使用场景。

### 2. 硬拦截 Gate 按 `recruitment_type` 分流
- **选择**: `校招` → 执行最严格的 2027 届 + 2026-07-01 后拦截；`社招` → 放宽届数，校验经验年限；`不限` → 跳过招聘类型拦截，仅执行发布时间校验。
- **替代方案**: 统一执行校招拦截。理由：不灵活，限制了社招场景。

### 3. 其余决策与 Reasons 和 Risks 保持不变
（JD 提取采用 Agent LLM 侧 Text Summarization；薪资/时间规则定义在 SOP；反爬降级按平台路由。）

## Risks / Trade-offs

- **[风险] `recruitment_type` 缺失时 Agent 可能误导用户选择** → **缓解方案**: SOP 中限定 Agent 只能提供 3 个明确选项（校招/社招/不限），不可自由输入。
- **[风险] 部分网页没写具体发布时间** → **缓解方案**: 若缺失但标明 "2027 届秋招"，视为满足；若均缺失，标记为 `single_source_unverified_date` 警示。
- **[风险] Agent 提取届数误判** → **缓解方案**: SOP 给出关键词清单（"2027届校招"通过；"2026届"、"社招"、"3年以上经验"拦截）。