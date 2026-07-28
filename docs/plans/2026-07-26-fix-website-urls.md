# 企业官网链接批量修复计划

> **Goal:** 将数据库中457家B级公司的BOSS直聘搜索链接全部替换为真实企业校招入口/官网链接

**现状：** DB中457家公司的`website`字段为 `https://www.zhipin.com/web/geek/job?query=公司名` 形式，完全无用。
**目标：** 替换为各公司官网校招页（如 `https://xxx.zhiye.com/Campus`）或官网招聘页。

---

## 策略

457家公司无法全部手动搜索，采用分层策略：

### 第一层：用已知模式批量映射（快速覆盖~40%）
大量公司使用智联/牛客/赛码等标准化校招系统，URL有规律：
- `xxx.zhiye.com/Campus` — 智联校招（最常用）
- `xxx.zhaopin.com` — 智联招聘
- `xxx.hotjob.cn` — 牛客校招
- `campushr.xxx.com` — 自建校招
- `wecruit.hotjob.cn` — 联合校招
- `careers.xxx.com` or `career.xxx.com` — 外企校招

### 第二层：按行业/地域批量搜索（Web搜索，覆盖~30%）
按行业分组（机器人、3D打印、医疗器械、消费电子等），批量搜各公司校招链接。

### 第三层：剩余公司逐个搜索（~30%）
剩余找不到的，用web_search逐个查询。

---

## 执行计划

### Phase 1: 批量映射（规则引擎）
**脚本:** `scripts\batch_fix_website_rules.py`
- 从DB读取所有B级公司（含BOSS URL）
- 对公司名做归一化（去括号、去英文名）
- 按规则生成URL：
  - `xxx.zhiye.com` 模式：公司名拼音/缩写 + `.zhiye.com/Campus`
  - 已知映射：hand-coded map for 50 known companies
- 验证URL可访问性（HEAD请求，非阻塞）
- 更新DB

### Phase 2: 批量搜索（并行子代理）
**脚本:** `scripts\batch_search_career_urls.py`
- 将公司按行业分组（机器人、3D打印、高端装备、医疗器械等）
- 每组派一个子代理去搜索校招链接
- 返回结果后写入DB

### Phase 3: 逐个补漏
- 剩余未覆盖的公司通过web_search逐个查询
- 使用codex CLI并行处理

---

## 技术细节

### DB连接
```python
import sqlite3
conn = sqlite3.connect(r'D:\DJTU\HermesWorkspace\career-tracker\data\tracker.db')
c = conn.cursor()
c.execute("SELECT id, name FROM companies WHERE website LIKE '%zhipin%'")
```

### 公司名归一化
```python
import re
def normalize(name):
    # "拓竹科技（Bambu Lab）" -> "拓竹科技"
    name = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
    # 去特殊字符
    return name
```

### URL验证
```python
import requests
try:
    r = requests.head(url, timeout=5, allow_redirects=True)
    return r.status_code < 400
except:
    return False
```

### 已知映射表（手动维护，覆盖头部公司）
```python
KNOWN_URLS = {
    '汇川技术': 'https://inovance.zhiye.com/Campus',
    '大疆创新': 'https://apply.careers.dji.com/campus-recruitment/dji/143359',
    '创想三维': 'https://creality.zhiye.com/campus/jobs',
    '拓竹科技': 'https://bambulab.jobs.feishu.cn/campus/',
    '纵维立方': 'https://www.anycubic.com',
    '智能派': 'https://www.elegoo.com.cn/index/join/index.html',
    '雷赛智能': 'https://www.leisai.com/recruitment/index.html',
    # ... 更多
}
```

---

## 执行顺序

1. 跑规则脚本（Phase 1）→ 覆盖~200家
2. 派并行子代理按行业搜索（Phase 2）→ 覆盖~150家  
3. 补漏（Phase 3）→ 覆盖剩余~100家
4. 验证：统计剩余BOSS URL数量