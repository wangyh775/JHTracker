from typing import Dict, Any, Optional, List, Union
import uuid
from src.logger import get_logger
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.models import ResumeItem, ResumeOptimizeRequest
from src.services.agent_executor import AgentExecutor
from src.services.resume_prompts import build_optimize_prompt

logger = get_logger("jhtracker.service.resume")

COMMON_TECH_KEYWORDS = [
    "Python", "FastAPI", "React", "TypeScript", "SQL", "MySQL", "PostgreSQL",
    "Redis", "Docker", "Kubernetes", "微服务", "架构设计", "高并发", "性能优化",
    "Go", "Golang", "Java", "Spring", "Kafka", "分布式", "Linux", "Git",
    "LLM", "Agent", "NLP", "PyTorch", "Vue", "前端", "后端", "全栈"
]

class ResumeService:
    def __init__(self, job_repo: Optional[Any] = None, user_repo: Optional[Any] = None, **kwargs):
        # 智能解构参数，兼容 positional 和各种 keyword 传参方式
        u_repo = kwargs.get("user_repo") or (job_repo if isinstance(job_repo, UserRepository) else user_repo)
        j_repo = kwargs.get("job_repo") or (user_repo if isinstance(user_repo, JobRepository) else job_repo)
        self.user_repo = u_repo
        self.job_repo = j_repo

    async def optimize_resume(
        self,
        resume_id: Union[str, ResumeOptimizeRequest],
        job_id: Optional[str] = None,
        job_description: Optional[str] = None,
        optimization_type: str = "GENERAL",
        target_company: Optional[str] = None,
        target_position: Optional[str] = None,
        engine: str = "auto",
        save_as_version: bool = False
    ) -> Dict[str, Any]:
        """
        简历优化与专岗 ATS 对齐。
        """
        # 兼容传入 ResumeOptimizeRequest 对象
        req_llm_config = None
        if isinstance(resume_id, ResumeOptimizeRequest):
            req = resume_id
            target_r_id = req.resume_id
            job_id = req.job_id
            job_description = req.job_description
            optimization_type = req.mode
            target_company = req.target_company
            target_position = req.target_position
            engine = req.engine
            save_as_version = req.save_as_version
            req_llm_config = req.llm_config
        else:
            target_r_id = resume_id

        resume = await self.user_repo.get_resume(target_r_id)
        if not resume:
            raise ValueError(f"Resume {target_r_id} not found")

        content = resume.content_md or ""

        # 1. 整理调优模式与目标实体
        resolved_company = target_company
        resolved_position = target_position
        resolved_jd = job_description

        # 若提供了 job_id，自动从公共库加载岗位详情
        if job_id:
            job = await self.job_repo.get_job(job_id)
            if job:
                resolved_company = resolved_company or job.company
                resolved_position = resolved_position or job.title
                resolved_jd = resolved_jd or job.description

        # 判定具体调优细分模式
        opt_type_upper = (optimization_type or "GENERAL").upper()
        if opt_type_upper in ("TARGETED", "CUSTOMIZED"):
            if resolved_company and resolved_position:
                scope_mode = "DUAL"
            elif resolved_company:
                scope_mode = "COMPANY"
            elif resolved_position:
                scope_mode = "POSITION"
            else:
                scope_mode = "GENERAL"
        else:
            scope_mode = "GENERAL"

        # 2. 构建 Prompt 并尝试调用本地智能体 CLI
        prompt = build_optimize_prompt(
            resume_md=content,
            mode=scope_mode,
            company=resolved_company,
            position=resolved_position,
            job_description=resolved_jd
        )

        agent_result: Optional[Dict[str, Any]] = None
        engine_display = "内置启发式规则引擎 (离线)"

        # 如果请求中未带 llm_config，尝试从 user_settings 中加载系统配置
        effective_llm_config = req_llm_config
        if not effective_llm_config:
            try:
                saved_cfg_str = await self.user_repo.get_setting("custom_llm_config")
                if saved_cfg_str:
                    import json
                    from src.models import LLMConfig
                    cfg_dict = json.loads(saved_cfg_str)
                    effective_llm_config = LLMConfig(**cfg_dict)
            except Exception as e:
                logger.warning(f"Failed to load saved custom_llm_config: {e}")

        # 尝试通过 AgentExecutor 执行
        try:
            agent_result = await AgentExecutor.execute_prompt(
                prompt=prompt,
                engine=engine,
                timeout=60.0,
                llm_config=effective_llm_config
            )
        except Exception as e:
            logger.warning(f"Error calling local agent executor: {e}, will fallback to builtin.")

        # 3. 整合结果 (若 Agent 成功返回则以 Agent 为准，否则走内置启发式规则兜底)
        if agent_result and isinstance(agent_result, dict) and "optimized_markdown" in agent_result:
            engine_display = agent_result.get("_engine_used", engine)
            ats_score = int(agent_result.get("ats_score", 85))
            match_level = agent_result.get("match_level", "HIGH" if ats_score >= 80 else "MEDIUM")
            matched_keywords = agent_result.get("matched_keywords", [])
            missing_keywords = agent_result.get("missing_keywords", [])
            suggestions = agent_result.get("suggestions", [])
            optimized_content = agent_result.get("optimized_markdown", content)
        else:
            # 内置启发式规则引擎兜底
            engine_display = "内置启发式规则引擎 (离线)"
            ats_score, match_level, matched_keywords, missing_keywords, suggestions, optimized_content = (
                self._fallback_rule_optimize(
                    content=content,
                    mode=scope_mode,
                    company=resolved_company,
                    position=resolved_position,
                    job_description=resolved_jd
                )
            )

        # 4. 版本安全隔离逻辑：若 save_as_version=True，存为独立 AI_OPTIMIZED 简历，不覆写原简历
        optimized_resume_id = None
        if save_as_version:
            parent_id = resume.parent_resume_id if resume.version_type == "AI_OPTIMIZED" and resume.parent_resume_id else resume.id
            
            # 生成易识别的标题后缀
            if scope_mode == "DUAL":
                version_tag = f"{resolved_company}-{resolved_position}"
            elif scope_mode == "COMPANY":
                version_tag = f"{resolved_company}专向"
            elif scope_mode == "POSITION":
                version_tag = f"{resolved_position}专岗"
            else:
                version_tag = "通用STAR优化"

            opt_title = f"{resume.title} (AI优化版 - {version_tag})"
            opt_id = f"res_ai_{uuid.uuid4().hex[:8]}"
            opt_skills = list(set((resume.parsed_skills or []) + [k for k in matched_keywords if k]))

            ai_resume = ResumeItem(
                id=opt_id,
                title=opt_title,
                category="CUSTOMIZED" if scope_mode != "GENERAL" else "GENERAL",
                file_path=resume.file_path,
                content_md=optimized_content,
                target_job_id=job_id,
                parsed_skills=opt_skills,
                is_default=False,
                version_type="AI_OPTIMIZED",
                parent_resume_id=parent_id
            )
            await self.user_repo.save_resume(ai_resume)
            optimized_resume_id = opt_id

        res: Dict[str, Any] = {
            "engine_used": engine_display,
            "optimization_scope": scope_mode,
            "ats_score": ats_score,
            "match_level": match_level,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "suggestions": suggestions,
            "optimized_markdown": optimized_content,
            "original_resume_id": resume.id,
            "original_version_type": getattr(resume, "version_type", "ORIGINAL"),
            "is_original_protected": True
        }

        if resolved_company:
            res["target_company"] = resolved_company
        if resolved_position:
            res["target_job"] = resolved_position
            res["target_position"] = resolved_position
        if optimized_resume_id:
            res["optimized_resume_id"] = optimized_resume_id
            res["ai_version_resume_id"] = optimized_resume_id

        return res

    def _fallback_rule_optimize(
        self,
        content: str,
        mode: str,
        company: Optional[str],
        position: Optional[str],
        job_description: Optional[str]
    ):
        """内置启发式规则诊断引擎 (无外部 CLI 依赖兜底)"""
        matched_keywords = []
        missing_keywords = []
        suggestions = []
        optimized_content = content
        ats_score = 82
        match_level = "HIGH"

        target_text = f"{position or ''} {company or ''} {job_description or ''}".lower()

        if mode in ("DUAL", "POSITION", "COMPANY") and target_text.strip():
            # 提炼技能交集
            candidate_keywords = [k for k in COMMON_TECH_KEYWORDS if k.lower() in target_text]
            if not candidate_keywords:
                candidate_keywords = ["Python", "FastAPI", "React", "微服务", "架构设计", "高并发"]

            matched_keywords = [k for k in candidate_keywords if k.lower() in content.lower()]
            missing_keywords = [k for k in candidate_keywords if k.lower() not in content.lower()]

            if mode == "DUAL":
                suggestions.append(f"【双向对齐】针对 {company} 的 {position} 岗位，建议将最匹配的技术栈在经历首段前置。")
            elif mode == "COMPANY":
                suggestions.append(f"【企业对齐】建议结合 {company} 核心技术基因强化工程规范与系统高可用描述。")
            elif mode == "POSITION":
                suggestions.append(f"【岗位对齐】针对 {position} 岗位要求，突出日常核心技术深度。")

            if missing_keywords:
                suggestions.append(f"【关键词补全】目标环境重点关注技能 [{', '.join(missing_keywords[:5])}]，建议在经历中量化补充。")
                optimized_content += (
                    f"\n\n<!-- 针对 {company or ''} {position or ''} 的建议补充 -->\n"
                    f"- 重点技术栈对齐：{', '.join(missing_keywords[:6])}\n"
                )
                ats_score = max(65, 88 - len(missing_keywords) * 4)
            else:
                ats_score = 90
        else:
            # 通用调优规则
            suggestions.append("【STAR 原则】建议遵循 情境(Situation)-任务(Task)-行动(Action)-结果(Result) 展开项目细节。")
            suggestions.append("【量化成果】避免简单列举'负责xxx开发'，使用具体百分比、QPS、节约工时等量化指标表达商业价值。")
            suggestions.append("【版面收敛】精简非相关过时技能，保持核心经历在 1-2 页 A4 内聚焦。")
            matched_keywords = [k for k in COMMON_TECH_KEYWORDS if k.lower() in content.lower()][:6]

            # 通用调优也要产出实质性的优化内容，而非原样返回
            # 在原文末尾追加 ATS 优化建议摘要区块，使优化后简历与原版有可辨识差异
            optimized_content = content
            ats_suggestions_block = "\n\n<!-- ===== ATS 通用调优建议摘要 ===== -->\n"
            ats_suggestions_block += "> **量化补充**: 建议为核心项目经历补充关键量化指标（如: 性能提升 X%、日活 X 万、响应时间降低 X ms）。\n"
            ats_suggestions_block += "> **关键词前置**: 将目标岗位高频技术关键词在技能清单中前置 1-2 位。\n"
            ats_suggestions_block += "> **STAR 结构**: 确保每段项目经历至少包含 情境→任务→行动→结果 四要素闭环。\n"
            if matched_keywords:
                ats_suggestions_block += f"> **已命中关键词**: {', '.join(matched_keywords)}\n"
            ats_suggestions_block += "<!-- ===== ATS 通用调优建议摘要 END ===== -->"
            optimized_content += ats_suggestions_block
            ats_score = 85

        match_level = "HIGH" if ats_score >= 80 else ("MEDIUM" if ats_score >= 65 else "LOW")
        return ats_score, match_level, matched_keywords, missing_keywords, suggestions, optimized_content
