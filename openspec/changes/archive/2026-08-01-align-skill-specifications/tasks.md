## 1. application-tracker Skill 对齐

- [x] 1.1 修正 `skills/application-tracker/SKILL.md` 状态流转图为 `Pending Approval` → 人类批准 → `待投递` → `已投递` → 后续面试/Offer 流程
- [x] 1.2 修正 SQL 示例中的 `'待投递'` 为 `'Pending Approval'`，并更新 channel 描述
- [x] 1.3 新增 Agent 只读防护声明段落（禁止改写 `POST_APPLY_STATUS_LIST` 中的记录）

## 2. candidate-profile-and-resume Skill 对齐

- [x] 2.1 在 `skills/candidate-profile-and-resume/SKILL.md` 的 Asset Locations 中增加 `enterprise_preference` 字段说明
- [x] 2.2 在 Resume Parsing 工作流中增加从简历中提取企业偏好并同步写入 `data/profile.md` 的步骤

## 3. 验证

- [x] 3.1 运行 `pytest` 确认无回归
- [x] 3.2 人工审查两个 Skill 文件确保状态流转与 `constants.py` 一致