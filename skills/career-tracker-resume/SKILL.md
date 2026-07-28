---
name: career-tracker-resume
description: "Resume version management (upload/preview/download). Invoke when user says '上传简历/简历管理/版本管理/查看简历版本/管理简历'."
---

# Career Tracker Resume Skill

Manages multiple resume versions in the database and filesystem.

## Prerequisites

- `data/tracker.db` — SQLite database
- Uploads folder: `data/resumes/`

## Workflow

### 1. Show existing resumes
```sql
SELECT id, name, version, file_path, file_type, file_size, is_default, created_at
FROM resumes ORDER BY created_at DESC;
```

### 2. Set default resume
```sql
-- Reset all to 0
UPDATE resumes SET is_default = 0;
-- Set target to 1
UPDATE resumes SET is_default = 1 WHERE id = ?;
```

### 3. Add new resume
When adding a new resume file, copy the file to `data/resumes/` with a unique hash filename to prevent overwrite, then insert metadata:
```sql
INSERT INTO resumes (name, version, file_path, file_type, file_size, is_default, note)
VALUES (?, ?, ?, ?, ?, ?, ?);
```