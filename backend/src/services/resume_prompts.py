from typing import Optional

def build_optimize_prompt(
    resume_md: Optional[str] = None,
    mode: str = "GENERAL",
    company: Optional[str] = None,
    position: Optional[str] = None,
    job_description: Optional[str] = None,
    resume_content: Optional[str] = None,
):
    content = resume_md or resume_content or ""
    """
    根据调优模式构建针对性的 Prompt。
    模式包括:
    - GENERAL: 通用调优 (STAR 法则、量化成果、消除废话)
    - COMPANY: 企业定向调优 (企业文化、业务特性、大厂技术基因与用人偏好)
    - POSITION: 岗位定向调优 (硬核 JD 关键词对齐、技能覆盖、核心业务对齐)
    - DUAL: 企业 + 岗位双重定向调优 (深度定制、最高精度 ATS 对齐)
    """
    base_instructions = """
你是一位兼具大厂技术专家与资深 HR 背景的求职 ATS 诊断与简历优化导师。
你的职责是基于给定的原始简历与目标背景，完成专业的 ATS 诊断分析并产出高质量的优化版 Markdown 简历。

【严格规则】：
1. 真实性第一：严禁凭空捏造未曾发生的公司或学历背景，只允许对已有的项目经历、工作成果、技能栈进行专业术语重构、逻辑提炼与 STAR 化展开。
2. 强化量化：在优化简历中，多使用量化指标与指标化语言（如性能提升百分比、QPS、降低延迟、团队规模、降本增效成果）。
3. 契约格式要求：【必须且仅输出】一个纯 JSON 对象，不要附加任何前后缀闲聊、引言或说明！
"""

    json_format_contract = """
请严格按照如下 JSON 结构返回（注意是合法的 JSON 字符串）：
{
  "ats_score": 85,
  "match_level": "HIGH",
  "matched_keywords": ["技能A", "技能B"],
  "missing_keywords": ["待补充技能C", "待补充经验D"],
  "suggestions": [
    "具体的诊断与修改建议1",
    "具体的诊断与修改建议2",
    "具体的诊断与修改建议3"
  ],
  "optimized_markdown": "# 优化后的完整简历正文（Markdown 格式）\\n..."
}
"""

    if mode == "DUAL":
        context_section = f"""
【调优模式】：专岗调优 —— 企业 + 岗位双重定向对齐
【目标企业】：{company or '未指定'}
【目标岗位】：{position or '未指定'}
【岗位 JD 详情】：
{job_description or '无详细 JD，请结合该企业通常对该岗位的行业标准要求对齐。'}

【专岗双重优化重点】：
1. 深度对齐目标企业的业务体量、技术选型偏好与工程规范。
2. 全面覆盖目标岗位 JD 中的高频核心硬技能与软实力要求。
3. 调整项目叙述次序与重点，把与该岗位最相关的经历置顶，并用贴近该企业业务语境的专业术语表达。
"""
    elif mode == "COMPANY":
        context_section = f"""
【调优模式】：专岗调优 —— 企业文化与业务基因定向对齐
【目标企业】：{company or '标杆大厂/头部企业'}

【企业定向优化重点】：
1. 分析该企业（如核心价值观、研发文化、技术栈基因、用人标准），针对性优化自我评价与核心优势。
2. 突出候选人的工程素养、Owner 意识、跨团队协作能力及解决高复杂度问题的潜力。
3. 让简历整体调性更加贴合该企业的招聘风貌。
"""
    elif mode == "POSITION":
        context_section = f"""
【调优模式】：专岗调优 —— 岗位硬核技能对齐
【目标岗位名称】：{position or '目标专业岗位'}
【岗位 JD 详情】：
{job_description or '请针对该标准岗位的业界通用招聘要求进行对齐。'}

【岗位定向优化重点】：
1. 提炼该岗位必须具备的核心硬核技术（编程语言、框架、系统架构、业务工具链）。
2. 在 missing_keywords 中明确标出原简历欠缺的关键技能点，并在 optimized_markdown 中通过合理上下文自然植入。
3. 重点对齐该岗位日常职责中要求的技术深度与广度。
"""
    else:  # GENERAL
        context_section = """
【调优模式】：通用调优 —— 母版简历 STAR 精炼与量化增强
【通用优化重点】：
1. 遵循 STAR 原则 (情境-任务-行动-结果) 重构所有项目与工作经历，消灭“负责日常开发”等假大空表述。
2. 强化动词与商业价值（如“主导设计”、“攻克瓶颈”、“重构架构”）。
3. 优化排版信息密度与层级结构，适合作为一份高通过率的基底通用母版。
"""

    prompt = f"""{base_instructions}
{context_section}

【候选人原始简历】：
```markdown
{content}
```

{json_format_contract}
"""
    if resume_content is not None:
        return prompt.strip(), mode
    return prompt.strip()

# Alias for compatibility with tests
build_resume_optimize_prompt = build_optimize_prompt
