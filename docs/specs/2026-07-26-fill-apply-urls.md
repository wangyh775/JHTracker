# Spec: 为S/A级公司补全具体岗位投递链接

## 现状

当前DB中 `companies.website` 字段存的是公司官网首页（如 `www.creality.com`）或校招入口（如 `inovance.zhiye.com/Campus`），不是具体岗位投递页。

**NDB需求：** 每个公司至少有一条 `applications` 记录，其 `url` 字段指向**具体岗位投递页面**（如 `bambulab.jobs.feishu.cn/campus/position/7644878107267057961/detail`）。

## 目标S/A公司（9家）

| 公司 | 当前website | 当前application url | 需要做什么 |
|------|-------------|-------------------|----------|
| 拓竹科技 | feishu校招首页 | ✅ 已有具体岗位链接 | 再找1-2个匹配岗位 |
| INTAMSYS | intamsys.com | ❌ 公司首页 | 找校招入口+具体岗位 |
| 大疆创新 | apply.careers.dji.com/... | ⚠️ 校招总入口 | 找具体岗位（控制算法/嵌入式） |
| 汇川技术 | inovance.zhiye.com/Campus | ⚠️ 校招总入口 | 找具体岗位 |
| 创想三维 | creality.zhiye.com/campus/jobs | ⚠️ 校招总入口 | 找具体岗位 |
| 纵维立方 | anycubic.com | ❌ 公司首页 | 找校招+具体岗位 |
| 智能派 | elegoo.com.cn | ❌ 招聘页 | 找校招+具体岗位 |
| 雷赛智能 | leisai.com/recruitment | ❌ 社招页 | 确认是否有校招 |

## 方法

用 Chrome DevTools（已在127.0.0.1:21561运行）或 `web_search` + `web_extract` 逐个攻破：

1. 对有.zhiye.com系统的：爬取职位列表页，找到具体职位的postId
2. 对有飞书校招的：爬取职位列表，找到具体position id
3. 对只有公司首页的：搜索校招页面URL，再爬具体职位

## 验证标准

- 每条application记录有具体岗位名（如"机电工程师"不是"校招综合岗"）
- 每条application的url指向具体岗位详情页（含position id）
- 公司website字段更新为校招入口（不是公司首页）