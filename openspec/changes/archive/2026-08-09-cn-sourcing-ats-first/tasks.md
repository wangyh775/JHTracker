# Tasks: cn-sourcing-ats-first

## 1. 数据模型与 Migration

- [ ] 1.1 在 `models.py` 的 `Application` 模型新增 `form_type` 与 `source_platform` 字段（String, nullable）
- [ ] 1.2 在 `migrations/versions/` 新增 Alembic migration：`add_form_type_and_source_platform_to_applications`
- [ ] 1.3 migration 必须幂等（使用 `inspect` 检查列是否存在再执行 `add_column`）
- [ ] 1.4 在 `tests/test_submission_models.py` 新增测试：验证字段写入与读取

## 2. ATS Fetcher 实现

- [ ] 2.1 新建 `services/sourcing/__init__.py`（空包标记）
- [ ] 2.2 新建 `services/sourcing/ats_fetcher.py`，定义 `AtsJob` dataclass 与 `FORM_TYPE_RULES` 常量
- [ ] 2.3 实现 `_fetch_beisen()`：POST `m.beisen.com/Api/JobSearch/SearchV2`，解析 `JobName/CompanyName/WorkPlaceName/SalaryStr/Url`
- [ ] 2.4 实现 `_fetch_moka()`：POST `app.mokahr.com/api/apply/spa/positions/search`，从 `company_slug` 提取 `orgId`
- [ ] 2.5 实现 `_fetch_nowcoder()`：GET `nowcoder.com/np/api/job/schooljobs/list`
- [ ] 2.6 实现 `_fetch_yingjiesheng()`：复用 `_fetch_beisen` 或抓列表页 HTML 解析
- [ ] 2.7 实现 `fetch_ats_jobs(provider, keyword, city, company_slug, page)` 统一入口，支持 `provider="all"` 并发
- [ ] 2.8 实现 `_identify_form_type(apply_url)`：按 `FORM_TYPE_RULES` 正则匹配，未命中返回 `open_question`
- [ ] 2.9 实现各适配器独立 try/except，单家失败返回空列表 + error 信息

## 3. MCP 工具注册

- [ ] 3.1 在 `mcp_server.py` 注册 `fetch_ats_jobs` 工具，参数与 design.md 定义一致
- [ ] 3.2 升级 `create_application` 工具：新增 `form_type` 与 `source_platform` 可选参数，写入 DB
- [ ] 3.3 升级 `get_application` 与 `list_applications`：返回结果包含 `form_type` 与 `source_platform`
- [ ] 3.4 在 `tests/test_mcp_server.py` 新增 `fetch_ats_jobs` 工具测试（mock 各 ATS 接口）

## 4. Skill 文档重写

- [ ] 4.1 重写 `skills/job-sourcing-and-scoring/SKILL.md`：
  - [ ] 4.1.1 新增 Layer 0（国内 ATS 直连）章节，定义调用 `fetch_ats_jobs` 的指令
  - [ ] 4.1.2 重排 Layer 1-4 顺序（Firecrawl → Exa/Tavily → CDP → webfetch）
  - [ ] 4.1.3 平台路由表二维化（enterprise_preference × job_scenario）
  - [ ] 4.1.4 新增 form_type 识别与传递步骤（sourcing → create_application → application-executor）
  - [ ] 4.1.5 新增 Layer 0 降级规则（≥3 条停止，<3 条降级 Layer 1）
  - [ ] 4.1.6 CDP 降级为 Layer 3 兜底，明确"仅前 3 层全空时触发"

## 5. 文档同步

- [ ] 5.1 更新 `docs/SKILLS_AND_MCP_GUIDE.md`：
  - [ ] 5.1.1 在 MCP Tools 列表新增 `fetch_ats_jobs` 条目（🔍 评估 类目下新增 🔎 岗位检索 子类目）
  - [ ] 5.1.2 在 4 大 Skills 表格中更新 `job-sourcing-and-scoring` 行的"对应 MCP 工具"列，加入 `fetch_ats_jobs`
  - [ ] 5.1.3 新增"国内 ATS 直连"小节，说明 Layer 0 的定位与使用场景
- [ ] 5.2 更新 `docs/architecture.md`：
  - [ ] 5.2.1 在 sourcing 架构图中新增 Layer 0（ATS 直连）节点
  - [ ] 5.2.2 更新分层检索协议描述，反映新 Layer 顺序
  - [ ] 5.2.3 新增 form_type 传递链路说明（sourcing → application → executor）

## 6. 测试验证

- [ ] 6.1 新建 `tests/test_ats_fetcher.py`：
  - [ ] 6.1.1 mock 4 个 ATS 接口响应，验证字段映射
  - [ ] 6.1.2 验证 `provider="all"` 并发去重逻辑
  - [ ] 6.1.3 验证单家失败不阻塞其他平台
  - [ ] 6.1.4 验证 form_type 识别规则覆盖所有域名特征
  - [ ] 6.1.5 验证 salary 为 "面议"/空时返回 None
- [ ] 6.2 新建 `tests/test_sourcing_skill.py`：
  - [ ] 6.2.1 验证 Layer 0 ≥3 条结果时不降级
  - [ ] 6.2.2 验证 Layer 0 <3 条结果时降级到 Layer 1
  - [ ] 6.2.3 验证二维路由表（enterprise_preference × job_scenario）
- [ ] 6.3 运行 `pytest tests/ -v` 全量回归，确保 160+ 测试全绿
- [ ] 6.4 验证 `form_type` 字段在 `create_application` → `get_application` 链路中正确持久化
