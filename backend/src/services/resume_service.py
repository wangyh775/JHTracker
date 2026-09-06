from typing import Dict, Any, Optional
import re
import uuid
from src.logger import get_logger
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.models import ResumeItem

logger = get_logger("jhtracker.service.resume")

class ResumeService:
    def __init__(self, job_repo: JobRepository, user_repo: UserRepository):
        self.job_repo = job_repo
        self.user_repo = user_repo

    async def optimize_resume(
        self,
        resume_id: str,
        job_id: Optional[str] = None,
        optimization_type: str = "GENERAL",
        save_as_version: bool = False
    ) -> Dict[str, Any]:
        """
        简历优化与专岗 ATS 对齐。
        重要规则：用户原始简历受只读保护，AI 优化建议生成独立 AI_OPTIMIZED 版本或仅返回润色建议，绝不覆写原始简历。
        """
        resume = await self.user_repo.get_resume(resume_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")

        content = resume.content_md or ""
        suggestions = []
        optimized_content = content
        matched_keywords = []
        missing_keywords = []
        target_company = None
        target_job = None
        ats_score = 85

        if optimization_type == "TARGETED" and job_id:
            job = await self.job_repo.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            target_company = job.company
            target_job = job.title

            # 提取岗位关键词并进行 ATS 契合度比对
            job_text = f"{job.title} {job.description or ''}"
            keywords = ["Python", "FastAPI", "React", "SQL", "Docker", "微服务", "架构设计", "高并发", "性能优化"]
            all_target_keywords = [k for k in keywords if k.lower() in job_text.lower()]
            matched_keywords = [k for k in all_target_keywords if k.lower() in content.lower()]
            missing_keywords = [k for k in all_target_keywords if k.lower() not in content.lower()]

            if missing_keywords:
                suggestions.append(f"检测到目标岗位重视技能 [{', '.join(missing_keywords)}]，建议在项目经验或专业技能中重点突出。")
                optimized_content += f"\n\n<!-- 针对 {job.company} - {job.title} 的专岗适配建议 -->\n- 重点对齐技术栈：{', '.join(missing_keywords)}\n"

            ats_score = 88 if not missing_keywords else 72
        else:
            # 通用 STAR 法则润色建议
            suggestions.append("建议遵循 STAR 法则 (情境-任务-行动-结果) 量化项目产出，多使用具体百分比和数据支撑。")
            suggestions.append("精简非核心技能，合并重复项目经历，控制在 1-2 页 A4 纸内。")
            ats_score = 85

        # 始终确保原始简历不被覆写；若保存版本，则存为独立的 AI_OPTIMIZED 简历记录
        optimized_resume_id = None
        if save_as_version:
            # 找到根原始简历 ID
            parent_id = resume.parent_resume_id if resume.version_type == "AI_OPTIMIZED" and resume.parent_resume_id else resume.id
            version_suffix = f" (AI优化版 - {target_job or '通用'})" if len(resume.title) < 40 else " (AI优化版)"
            opt_title = f"{resume.title}{version_suffix}"
            opt_id = f"res_ai_{uuid.uuid4().hex[:8]}"
            opt_skills = list(set((resume.parsed_skills or []) + [k for k in missing_keywords if k]))

            ai_resume = ResumeItem(
                id=opt_id,
                title=opt_title,
                category="CUSTOMIZED" if optimization_type == "TARGETED" else "GENERAL",
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
            "ats_score": ats_score,
            "suggestions": suggestions,
            "optimized_markdown": optimized_content,
            "original_resume_id": resume.id,
            "original_version_type": getattr(resume, "version_type", "ORIGINAL"),
            "is_original_protected": True
        }
        if target_company:
            res["target_company"] = target_company
            res["target_job"] = target_job
            res["matched_keywords"] = matched_keywords
            res["missing_keywords"] = missing_keywords
        if optimized_resume_id:
            res["optimized_resume_id"] = optimized_resume_id
            res["ai_version_resume_id"] = optimized_resume_id

        return res
