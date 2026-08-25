# JHTracker 2.0 REST API 接口规范与数据字典

## 1. 协议规范

- **通信协议**：HTTP/1.1 RESTful JSON
- **默认端口**：FastAPI 后端 `5000` 端口；前端 Vite 开发服务 `5173` 端口（代理 `/api` 至 `http://127.0.0.1:5000`）
- **全局前缀**：`/api/v1`
- **通用响应格式**：
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

---

## 2. 核心 REST API 端点

### 2.1 投递工作台 (`/api/v1/applications`)

| 方法 | 路径 | 描述 | 请求参数 / Body | 响应数据 |
|---|---|---|---|---|
| `GET` | `/api/v1/applications` | 获取投递列表（分页、多字段筛选、活跃/归档隔离） | `is_archived` (bool, 默认 false), `status`, `track`, `search`, `page`, `page_size` | `{ "items": List[ApplicationOut], "total": int, "active_count": int, "archived_count": int }` |
| `POST` | `/api/v1/applications` | 新建投递记录 | `ApplicationCreate` (JSON) | `ApplicationOut` |
| `GET` | `/api/v1/applications/{id}` | 获取单条投递详情（含公司、岗位、预填与面试反馈关联） | 无 | `ApplicationDetailOut` |
| `PUT` | `/api/v1/applications/{id}` | 更新投递记录（状态流转、薪资、面试日期等） | `ApplicationUpdate` (JSON) | `ApplicationOut` |
| `DELETE` | `/api/v1/applications/{id}` | 删除投递记录 | `confirm` (bool, 必须为 true) | `{ "success": true }` |
| `POST` | `/api/v1/applications/{id}/archive` | 归档指定投递记录 | 无 | `ApplicationOut` (`is_archived=True`) |
| `POST` | `/api/v1/applications/{id}/unarchive` | 恢复指定投递记录至活跃池 | 无 | `ApplicationOut` (`is_archived=False`) |
| `POST` | `/api/v1/applications/archive-stale` | 批量自动归档长期无状态更新的记录 | `{ "days_threshold": 15 }` | `{ "archived_count": int, "affected_ids": List[int] }` |

### 2.2 待投递机会池 (`/api/v1/to-apply`)

| 方法 | 路径 | 描述 | 请求参数 / Body | 响应数据 |
|---|---|---|---|---|
| `GET` | `/api/v1/to-apply` | 获取高匹配待投递机会池列表（带 4 轨推断与话术） | `track`, `min_score`, `search` | `List[ToApplyJobOut]` |
| `POST` | `/api/v1/to-apply/{id}/prefill` | 触发指定岗位的 Zero-Submit 预填审计流程 | `{ "resume_track": "control", "cdp_url": "http://127.0.0.1:9222" }` | `AutofillResponse` |

### 2.3 Zero-Submit 网申预填核对站 (`/api/v1/submissions`)

| 方法 | 路径 | 描述 | 请求参数 / Body | 响应数据 |
|---|---|---|---|---|
| `GET` | `/api/v1/submissions` | 获取预填记录列表（按审计状态过滤） | `status` (pending_audit/submitted/rejected), `page` | `List[SubmissionOut]` |
| `GET` | `/api/v1/submissions/{id}` | 获取指定预填表单快照详情（DOM 字段键值对） | 无 | `SubmissionDetailOut` |
| `PUT` | `/api/v1/submissions/{id}` | 更新预填字段草稿 | `SubmissionUpdate` (JSON) | `SubmissionOut` |
| `POST` | `/api/v1/submissions/{id}/confirm` | 确认手动已提交（回写 application 状态为已投递） | 无 | `ApplicationOut` |

### 2.4 面试反馈与偏好记忆 (`/api/v1/feedbacks`, `/api/v1/memories`)

| 方法 | 路径 | 描述 | 请求参数 / Body | 响应数据 |
|---|---|---|---|---|
| `GET` | `/api/v1/feedbacks` | 获取面试反馈列表 | `application_id` (可选) | `List[InterviewFeedbackOut]` |
| `POST` | `/api/v1/feedbacks` | 录入面试反馈或复盘记录 | `InterviewFeedbackCreate` (JSON) | `InterviewFeedbackOut` |
| `GET` | `/api/v1/memories` | 获取智能体负向规则与偏好记忆 | `category` (company/job/location) | `List[MemoryOut]` |
| `POST` | `/api/v1/memories` | 新增偏好/排他规则 | `MemoryCreate` (JSON) | `MemoryOut` |

### 2.5 路由与设置 (`/api/v1/router`, `/api/v1/settings`)

| 方法 | 路径 | 描述 | 请求参数 / Body | 响应数据 |
|---|---|---|---|---|
| `POST` | `/api/v1/router/match` | 实时计算岗位所属 4 轨分类与推荐简历话术 | `{ "job_title": "str", "job_description": "str" }` | `TrackMatchResult` |
| `GET` | `/api/v1/settings` | 获取系统配置（自动归档天数阈值、CDP 端口等） | 无 | `SettingsOut` |
| `PUT` | `/api/v1/settings` | 更新系统配置 | `SettingsUpdate` (JSON) | `SettingsOut` |

---

## 3. 数据字典

### 3.1 `applications` (投递主表)
- `id` (INT, PK): 唯一主键
- `company_id` (INT, FK -> companies.id): 所属公司 ID
- `job_id` (INT, FK -> jobs.id, Nullable): 所属职位 ID
- `position` (VARCHAR(100)): 投递岗位名称
- `status` (VARCHAR(30)): 状态（待投递/预填待审/已投递/笔试/面试/收到Offer/已拒绝/已归档）
- `track` (VARCHAR(30)): 4 轨分类（`control` / `embedded_auto` / `mechatronics` / `mechanical_cfd`）
- `apply_date` (DATETIME): 投递日期
- `resume_version` (VARCHAR(50)): 使用的简历版本（控制算法版/自动化嵌入式版/机电电气版/机械结构仿真版/通用版）
- `resume_id` (INT, FK -> resumes.id, Nullable): 绑定的简历文件 ID
- `form_type` (VARCHAR(30)): 网申表单类型（`structured` / `open_question` / `attachment` / `one_click`）
- `source_platform` (VARCHAR(50)): 招聘渠道来源（如 北森 / Moka / 牛客 / BOSS / 国聘）
- `source_url` (VARCHAR(500)): 招聘或投递原始链接
- `match_score` (FLOAT): AI 匹配度评分 (0-100)
- `scoring_reason` (TEXT): 匹配评分细则与理由
- `is_archived` (BOOLEAN, default False): 是否归档标记
- `archived_at` (DATETIME): 归档时间戳
- `deadline` (DATETIME): 截止投递日期
- `interview_date` (DATETIME): 最新面试时间
- `offer_salary` (VARCHAR(50)): Offer 薪资
- `notes` (TEXT): 备注与追踪记录
- `created_at` (DATETIME), `updated_at` (DATETIME)

### 3.2 `application_submissions` (Zero-Submit 预填快照表)
- `id` (INT, PK): 唯一主键
- `application_id` (INT, FK -> applications.id): 关联投递记录
- `portal_url` (VARCHAR(500)): 招聘网申入口 URL
- `status` (VARCHAR(30)): 审计状态 (`pending_audit` / `submitted` / `rejected` / `failed`)
- `filled_fields_count` (INT): 成功注入字段数量
- `fields_json` (TEXT): 预填表单字段名与注入值的 JSON 字典
- `screenshot_path` (VARCHAR(255)): 页面预填后截屏保存路径
- `resume_used` (VARCHAR(100)): 本次预填使用的简历版本/文件名
- `error_message` (TEXT): 执行异常信息（若失败）
- `created_at` (DATETIME), `updated_at` (DATETIME)

### 3.3 `interview_feedbacks` (面试反馈与复盘表)
- `id` (INT, PK): 唯一主键
- `application_id` (INT, FK -> applications.id): 关联投递记录
- `round_number` (INT): 面试轮次 (1/2/3/HR面)
- `interview_date` (DATETIME): 面试日期
- `interviewer_info` (VARCHAR(100)): 面试官信息/岗位
- `technical_questions` (TEXT): 考察专业技术问题集与回答情况
- `project_deep_dive` (TEXT): 项目深挖细节
- `candidate_questions` (TEXT): 反问环节问题
- `result_status` (VARCHAR(30)): 结果（通过/待定/未通过）
- `reflection_notes` (TEXT): 自身表现复盘与改进要点
- `created_at` (DATETIME)

### 3.4 `memories` (智能体负向规则与偏好记忆表)
- `id` (INT, PK): 唯一主键
- `category` (VARCHAR(50)): 规则类型（`company_blacklist` / `location_preference` / `salary_floor` / `track_focus`）
- `target_name` (VARCHAR(100)): 规则主体
- `rule_content` (TEXT): 详细偏好或排他规则描述
- `weight` (FLOAT, default 1.0): 权重因子
- `is_active` (BOOLEAN, default True): 是否生效
- `created_at` (DATETIME)
