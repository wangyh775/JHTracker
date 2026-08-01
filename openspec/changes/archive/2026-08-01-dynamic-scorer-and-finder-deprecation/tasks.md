## 1. ai_scorer 动态预筛改造

- [x] 1.1 在 `scripts/ai_scorer.py` 中增加 `load_dynamic_negative_rules(conn)` 函数读取 `memories` 数据库表
- [x] 1.2 修改 `prefilter()` 和 `score_batch()` 逻辑，使 Stage 1 预筛能使用动态负向记忆规则淘汰不匹配公司

## 2. 脚本废弃拦截

- [x] 2.1 在 `scripts/daily_new_company_finder.py` 头部添加废弃声明与拦截提示，执行时通过 `sys.exit(0)` 退出

## 3. 验证

- [x] 3.1 运行测试套件 (`pytest`) 验证更新无破坏
- [x] 3.2 运行 `python scripts/daily_new_company_finder.py` 验证拦截提示正确触发
- [x] 3.3 运行 `python scripts/ai_scorer.py --dry-run` 验证动态记忆预筛正常加载