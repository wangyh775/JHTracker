---
name: "candidate-profile-and-resume"
description: "Manages candidate career profile (data/profile.md), resume documents, preferences, and negative memory constraints. Alias: career-tracker-profile, career-tracker-resume."
allowed-tools:
  - JHTracker:get_candidate_profile
  - JHTracker:get_user_preferences
---

# Candidate Profile and Resume Skill

Manages candidate assets, career preferences, resume documents, and negative memory rules in JHTracker.

## Trigger Scenarios

Invoke when the user says any of:
- "查看/更新我的简历" / "更新个人求职偏好"
- "添加排除规则" / "查看黑名单记忆"
- "view my profile" / "manage candidate preferences"

## Asset Locations

- **Profile File**: `data/profile.md` — Candidate target roles, skills, expected salary, target cities.
- **Resumes Directory**: `data/resumes/` — Candidate PDF/Word resume versions.
- **Negative Memories**: `memories` database table — Excluded tech stacks, undesirable company cultures, user rejection feedback.

## Key Operations

1. **Read Profile**: Call `JHTracker:get_candidate_profile()` or read `data/profile.md`.
2. **Read Preferences & Negative Memories**: Call `JHTracker:get_user_preferences()` to inspect active rules and recent rejection notes.
3. **Parse Resumes**: Extract text from PDF files in `data/resumes/` to sync candidate experience into Agent context.
