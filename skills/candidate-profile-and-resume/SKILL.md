---
name: "candidate-profile-and-resume"
description: "Manages candidate career profile (data/profile.md), resume documents, preferences, and negative memory constraints. Alias: career-tracker-profile, career-tracker-resume."
allowed-tools:
  - JHTracker:get_candidate_profile
  - JHTracker:update_candidate_profile
  - JHTracker:get_user_preferences
  - JHTracker:list_resumes
  - JHTracker:get_default_resume
  - JHTracker:add_memory_rule
  - JHTracker:delete_memory_rule
---

# Candidate Profile and Resume Skill

Manages candidate assets, career preferences, resume documents, and negative memory rules in JHTracker.

## Trigger Scenarios

Invoke when the user says any of:
- "查看/更新我的简历" / "根据简历更新个人求职偏好"
- "添加排除规则" / "查看黑名单记忆"
- "view my profile" / "manage candidate preferences / update profile from resume"

## Asset Locations

- **Profile File**: `data/profile.md` — Candidate target roles, skills, expected salary, target cities, and `enterprise_preference` (央国企/外企/民企/不限).
- **Resumes Directory**: `data/resumes/` — Candidate PDF/Word resume versions.
- **Negative Memories**: `memories` database table — Excluded tech stacks, undesirable company cultures, user rejection feedback.

## Key Operations & Resume Sync Workflow

1. **Read Profile**: Call `JHTracker:get_candidate_profile()` or read `data/profile.md`.
2. **Read Preferences & Negative Memories**: Call `JHTracker:get_user_preferences()` to inspect active rules and recent rejection notes.
3. **Parse Resume & Update Profile**:
   - Extract text from uploaded PDF/DOCX files in `data/resumes/`.
   - Structure text into standard Markdown sections (`教育背景`, `核心技术栈`, `项目经验`, `目标岗位`, `求职偏好`).
   - **Extract enterprise preference**: If the resume or user input indicates a preference for 央国企/外企/民企, parse and set the `enterprise_preference` field accordingly. If no preference is detected, default to `不限`.
   - Call `JHTracker:update_candidate_profile(content=...)` to update `data/profile.md`, ensuring the `enterprise_preference` field is included in the `求职偏好` section.
