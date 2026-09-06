from typing import List, Dict, Any, Optional, Set, Union
from datetime import datetime
import json
import math
import re
import uuid
from collections import defaultdict
from src.logger import get_logger
from src.models import JobItem, FeedbackRequest, ApplicationItem, KeywordMatrix
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.classifier import extract_job_categories, extract_primary_city

logger = get_logger("jhtracker.service.recommendation")

# 默认基础 IDF 近似权重表（仅当简历未生成结构化关键词矩阵时作为兜底冷启动）
DEFAULT_FALLBACK_SKILL_WEIGHTS: Dict[str, float] = {
    "solidworks": 2.5, "eplan": 2.5, "ansys": 2.5, "fluent": 2.5,
    "cfd": 2.4, "有限元": 2.4, "热流耦合": 2.5, "fdm": 2.5,
    "3d打印": 2.5, "增材制造": 2.5, "mpc": 2.2, "温控": 2.2,
    "机电一体化": 2.0, "stm32": 2.0, "单片机": 2.0, "机械设计": 2.0,
    "机械工程": 2.0, "结构设计": 2.0, "结构工程师": 2.0, "热设计": 2.2,
    "热管理": 2.2, "散热": 2.0, "嵌入式": 1.8, "cad": 1.6, "cam": 1.6,
    "c++": 1.2, "c": 1.0, "python": 1.0, "linux": 1.0, "git": 0.5,
    "pytorch": 2.2, "tensorflow": 2.0, "ros": 2.2, "ros2": 2.4,
    "fastapi": 2.0, "django": 1.8, "spring": 2.0, "vue": 1.8, "react": 1.8
}

class RecommendationService:
    def __init__(self, job_repo: JobRepository, user_repo: UserRepository):
        self.job_repo = job_repo
        self.user_repo = user_repo

    async def get_recommendations(
        self,
        resume_id: Optional[str] = None,
        min_score: float = 0.5,
        limit: int = 20,
        since_date: Optional[str] = None,
        max_jobs_per_company: int = 3
    ) -> List[Dict[str, Any]]:
        # 1. 获取简历对象及关键词矩阵/技能池
        target_resume = None
        keywords_matrix = None
        user_skills = set()

        if resume_id:
            target_resume = await self.user_repo.get_resume(resume_id)
        else:
            target_resume = await self.user_repo.get_default_resume()

        if target_resume:
            keywords_matrix = target_resume.keywords_matrix
            if target_resume.parsed_skills:
                user_skills = set([s.lower() for s in target_resume.parsed_skills])
        else:
            resumes = await self.user_repo.list_resumes()
            for r in resumes:
                if not keywords_matrix and r.keywords_matrix:
                    keywords_matrix = r.keywords_matrix
                if r.parsed_skills:
                    for s in r.parsed_skills:
                        user_skills.add(s.lower())

        # 2. 获取已有的反馈与 HITL 权重
        weights = await self.user_repo.get_feature_weights()
        feedback_list = await self.user_repo.list_feedback()
        handled_job_ids = {f["job_id"] if isinstance(f, dict) else f.job_id for f in feedback_list}

        # 核心去重与频控：已投递企业黑名单、待投递企业上限集合
        app_status = await self.user_repo.get_company_application_status(max_pending_limit=max_jobs_per_company)
        applied_companies = app_status.get("applied_companies", set())
        capped_pending_companies = app_status.get("capped_pending_companies", set())
        pending_counts = app_status.get("pending_counts", {})

        # 3. 多路动态召回（关键词矩阵核心/领域词 + 偏好高权城市/行业 + 最新时效）
        candidate_map = {}

        # 准备关键词哈希表 (运行时编译)
        core_keywords_map = {}
        domain_keywords_map = {}
        base_keywords_map = {}
        negative_keywords_map = {}

        if keywords_matrix and keywords_matrix.categories:
            for item in keywords_matrix.categories.core:
                if item.enabled and item.keyword.strip():
                    core_keywords_map[item.keyword.strip().lower()] = float(item.weight)
            for item in keywords_matrix.categories.domain:
                if item.enabled and item.keyword.strip():
                    domain_keywords_map[item.keyword.strip().lower()] = float(item.weight)
            for item in keywords_matrix.categories.base:
                if item.enabled and item.keyword.strip():
                    base_keywords_map[item.keyword.strip().lower()] = float(item.weight)
            for item in keywords_matrix.categories.negative:
                if item.enabled and item.keyword.strip():
                    negative_keywords_map[item.keyword.strip().lower()] = float(item.weight)

        # 召回路 1: 核心技能 / 领域词检索
        search_terms = []
        if core_keywords_map:
            sorted_cores = sorted(core_keywords_map.items(), key=lambda x: x[1], reverse=True)
            search_terms.extend([k for k, _ in sorted_cores[:6]])
        if domain_keywords_map:
            sorted_domains = sorted(domain_keywords_map.items(), key=lambda x: x[1], reverse=True)
            search_terms.extend([k for k, _ in sorted_domains[:3]])

        # 兜底：若无关键词矩阵，退化使用原始技能召回
        if not search_terms and user_skills:
            sorted_skills = sorted(list(user_skills), key=lambda s: DEFAULT_FALLBACK_SKILL_WEIGHTS.get(s, 1.0), reverse=True)
            search_terms = sorted_skills[:6]

        for term in search_terms:
            try:
                s_jobs, _ = await self.job_repo.search_jobs(keyword=term, since_date=since_date, limit=60)
                for j in s_jobs:
                    candidate_map[j.id] = j
            except Exception:
                pass

        # 召回路 2: 偏好高权城市与行业召回 (权重 > 1.25)
        high_weight_cities = [k.replace("city:", "") for k, v in weights.items() if k.startswith("city:") and v >= 1.25]
        for c in high_weight_cities[:2]:
            try:
                c_jobs, _ = await self.job_repo.search_jobs(location=c, since_date=since_date, limit=40)
                for j in c_jobs:
                    candidate_map[j.id] = j
            except Exception:
                pass

        # 召回路 3: 最新时效岗位兜底
        recent_jobs, _ = await self.job_repo.search_jobs(since_date=since_date, limit=120)
        for j in recent_jobs:
            candidate_map[j.id] = j

        jobs = list(candidate_map.values())

        # 4. 双塔精排与打分
        candidates = []
        ideal_core_weight = max(1.0, sum(core_keywords_map.values()) * 0.5) if core_keywords_map else 5.0

        for job in jobs:
            # 跳过用户已经明确接受或拒绝过的岗位
            if job.id in handled_job_ids:
                continue

            # 规则1：已投递的企业彻底拉黑，不再推荐
            if job.company in applied_companies:
                continue

            # 规则2：待投递列表中已存在 >= max_jobs_per_company 个岗位的企业，不再推荐
            if job.company in capped_pending_companies:
                continue

            job_text = f"{job.title} {job.description or ''}".lower()
            job_title_lower = job.title.lower()

            # --- 塔 1: 能力基准分计算 (Base Ability) ---
            matched_cores = []
            matched_domains = []
            matched_bases = []

            if core_keywords_map or domain_keywords_map or base_keywords_map:
                # 具备关键词矩阵时的结构化打分
                score_core = 0.0
                for kw, w in core_keywords_map.items():
                    if kw in job_text:
                        score_core += w
                        matched_cores.append(kw)

                score_domain = 0.0
                for kw, w in domain_keywords_map.items():
                    if kw in job_text:
                        score_domain += w
                        matched_domains.append(kw)

                score_base = 0.0
                for kw, w in base_keywords_map.items():
                    if kw in job_text:
                        score_base += w
                        matched_bases.append(kw)

                raw_ability = score_core * 1.0 + score_domain * 0.75 + score_base * 0.3
                if raw_ability > 0:
                    ability_ratio = min(1.0, raw_ability / ideal_core_weight)
                    base_ability = 0.45 + 0.45 * ability_ratio
                else:
                    base_ability = 0.40
            elif user_skills:
                # 兼容旧版纯技能列表兜底
                total_skill_weight = sum(DEFAULT_FALLBACK_SKILL_WEIGHTS.get(s, 1.0) for s in user_skills)
                matched_skill_weight = sum(DEFAULT_FALLBACK_SKILL_WEIGHTS.get(s, 1.0) for s in user_skills if s in job_text)
                if matched_skill_weight > 0:
                    weighted_ratio = min(1.0, matched_skill_weight / max(1.0, total_skill_weight * 0.45))
                    base_ability = 0.50 + 0.40 * weighted_ratio
                else:
                    base_ability = 0.40
            else:
                base_ability = 0.50  # 无任何简历输入时的基准分

            # 负向词一票否决与惩罚（由矩阵 negative 动态判定）
            negative_penalty = 1.0
            negative_hit = None
            if negative_keywords_map:
                for neg_kw, penalty in negative_keywords_map.items():
                    if neg_kw in job_title_lower:
                        negative_penalty = min(negative_penalty, penalty)
                        negative_hit = neg_kw
                        break
                    elif neg_kw in job_text:
                        negative_penalty = min(negative_penalty, min(1.0, penalty + 0.35))
                        negative_hit = neg_kw

            # --- 塔 2: 意向偏好乘数计算 (Preference Multiplier) ---
            categories = extract_job_categories(job.title, job.description)
            cat_weights = [weights.get(f"category:{c}", 1.0) for c in categories]
            w_cat = (sum(cat_weights) / len(cat_weights)) if cat_weights else 1.0

            if job.industry and job.industry not in ["综合", "其他", "科技"]:
                w_ind = weights.get(f"industry:{job.industry}", 1.0)
            else:
                w_ind = 1.0

            city = extract_primary_city(job.location)
            w_city = weights.get(f"city:{city}", 1.0) if city else 1.0

            # 线性复合权重: 职能 50% + 行业 25% + 城市 25%
            raw_multiplier = 0.50 * w_cat + 0.25 * w_ind + 0.25 * w_city

            # 双曲正切平滑防过冲: 1.0 + 0.35 * tanh(raw_multiplier - 1.0)
            preference_bonus = 1.0 + 0.35 * math.tanh(raw_multiplier - 1.0)

            # 最终复合得分
            score = base_ability * preference_bonus * negative_penalty

            # 极值安全防护
            if math.isnan(score) or math.isinf(score):
                score = 0.40
            final_score = round(min(1.0, max(0.0, score)), 2)

            if final_score >= min_score:
                # 动态生成富有解释性的推荐理由
                reason_parts = []
                if matched_cores:
                    reason_parts.append(f"命中核心技能 [{', '.join(matched_cores[:3])}]")
                if matched_domains:
                    reason_parts.append(f"契合研究方向 [{', '.join(matched_domains[:2])}]")
                if not reason_parts and categories:
                    reason_parts.append(f"契合【{' / '.join(categories)}】职能")
                if not reason_parts:
                    reason_parts.append("符合近期活跃招聘画像")

                reason = "；".join(reason_parts)
                candidates.append({
                    "job": job.model_dump(),
                    "score": final_score,
                    "match_score": final_score,
                    "reason": reason,
                    "recommend_reason": reason,
                    "categories": categories,
                    "city": city,
                    "matched_skills": matched_cores + matched_domains,
                    "negative_hit": negative_hit
                })

        # 按得分从高到低排序
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # 5. 限制同企业在推荐列表中的配额（综合考虑待投递区已有数量）
        company_rec_counts = defaultdict(int)
        diverse_recommendations = []
        for item in candidates:
            company = item["job"]["company"]
            existing_pending = pending_counts.get(company, 0)
            # 允许推荐数量 = max_jobs_per_company - 已在待投递区的数量
            allowed_slots = max(0, max_jobs_per_company - existing_pending)
            
            if company_rec_counts[company] < allowed_slots:
                diverse_recommendations.append(item)
                company_rec_counts[company] += 1
            if len(diverse_recommendations) >= limit:
                break

        return diverse_recommendations

    async def record_feedback(
        self,
        job_id: str,
        action: str,
        reject_reasons: Optional[List[str]] = None,
        match_score: Optional[float] = None,
        recommend_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        人在环路反馈：
        - ACCEPT: 自动加入待投递流水线 (PENDING_APPLY)，提高该岗位类型、企业性质、行业与城市权重
        - REJECT: 降低该岗位类型、企业性质、行业与城市权重（不扣减具体企业）
        """
        job = await self.job_repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # 提取当前岗位的特征维度
        categories = extract_job_categories(job.title, job.description)
        city = extract_primary_city(job.location)

        # 记录反馈日志并更新权重
        feedback_req = FeedbackRequest(
            job_id=job_id,
            match_score=match_score if match_score is not None else (1.0 if action == "ACCEPT" else 0.0),
            recommend_reason=recommend_reason or ("AI 智能推荐匹配" if action == "ACCEPT" else "User manual feedback"),
            action=action,
            reject_reasons=reject_reasons or []
        )
        await self.user_repo.record_feedback(
            feedback=feedback_req,
            job_company=job.company,
            job_tags=job.type_tags or [],
            job_industry=job.industry,
            job_categories=categories,
            job_city=city
        )

        if action == "ACCEPT":
            # 自动进入待投递面板
            app_item = ApplicationItem(
                id=f"app_{uuid.uuid4().hex[:16]}",
                job_id=job.id,
                company=job.company,
                title=job.title,
                status="PENDING_APPLY",
                channel=job.source_site or "AI_RECOMMEND",
                match_score=match_score if match_score is not None else 0.88,
                recommend_reason=recommend_reason or "AI 智能推荐匹配"
            )
            await self.user_repo.create_or_update_application(app_item)

        return {"success": True, "status": "SUCCESS", "action": action, "job_id": job_id}

    async def sync_features_from_jobs(self, jobs: List[JobItem]) -> int:
        """
        特征元数据同步 Hook：从一批岗位（如刚爬取的、或MCP外部写入的）中萃取 category / industry / city，
        并增量注册到用户的 feature_weights 字典中（初始基准权重 1.0）。
        返回新增注册的特征数。
        """
        if not jobs:
            return 0
        features_to_register = []
        for job in jobs:
            # 1. 岗位职能类型
            for cat in extract_job_categories(job.title, job.description):
                features_to_register.append((f"category:{cat}", "category"))
            # 2. 垂直行业
            if job.industry and job.industry not in ["综合", "其他", "科技"]:
                features_to_register.append((f"industry:{job.industry}", "industry"))
            # 3. 期望城市
            city = extract_primary_city(job.location)
            if city:
                features_to_register.append((f"city:{city}", "city"))

        # 去重后增量注册
        unique_features = list({f[0]: f for f in features_to_register}.values())
        return await self.user_repo.batch_register_feature_metadata(unique_features)

    async def sync_all_features_from_public_db(self, min_industry_count: int = 10, min_city_count: int = 20) -> Dict[str, Any]:
        """
        全库特征元数据扫描与增量冷启动（Bootstrap）：
        直接从 public_jobs.db 中对 2.4万+ 岗位做聚合统计，提取高频垂直行业与核心城市，
        以及预设的 8 大标准岗位职能类型，安全幂等初始化到 user_data.db 的 feature_weights 中（1.0x 基准）。
        """
        import aiosqlite
        from collections import Counter
        from src.classifier import JOB_CATEGORY_RULES

        features_to_register = []

        # 1. 预设标准岗位大类（全量覆盖）
        for cat_name in JOB_CATEGORY_RULES.keys():
            features_to_register.append((f"category:{cat_name}", "category"))

        # 2. 扫描 public_jobs.db
        industry_counter = Counter()
        city_counter = Counter()
        from src.db import get_public_db

        async with get_public_db(self.job_repo.db_path) as db:
            async with db.execute("SELECT industry, location FROM jobs") as cursor:
                async for row in cursor:
                    ind_raw, loc_raw = row[0], row[1]
                    if ind_raw:
                        for p in ind_raw.replace("，", ",").split(","):
                            clean_ind = p.strip()
                            if clean_ind and clean_ind not in ("-", "其他", "综合", "科技", "上市公司", "民企", "央企国企"):
                                industry_counter[clean_ind] += 1
                    if loc_raw:
                        for p in loc_raw.replace("，", ",").split(","):
                            c = extract_primary_city(p)
                            if c and len(c) >= 2 and not c.endswith("、") and c not in ("全国", "不限", "其他", "待定", "海外"):
                                city_counter[c] += 1

        # 筛选有效频次行业
        for ind, cnt in industry_counter.items():
            if cnt >= min_industry_count:
                features_to_register.append((f"industry:{ind}", "industry"))

        # 筛选核心地级市
        for city, cnt in city_counter.items():
            if cnt >= min_city_count:
                features_to_register.append((f"city:{city}", "city"))

        unique_features = list({f[0]: f for f in features_to_register}.values())
        new_registered = await self.user_repo.batch_register_feature_metadata(unique_features)

        return {
            "total_extracted": len(unique_features),
            "new_registered": new_registered,
            "categories_count": len(JOB_CATEGORY_RULES),
            "industries_count": sum(1 for f in unique_features if f[1] == "industry"),
            "cities_count": sum(1 for f in unique_features if f[1] == "city")
        }

    async def validate_and_ground_matrix(self, matrix: Union[KeywordMatrix, dict]) -> Dict[str, Any]:
        """
        全量数据库接地性校验 (Pre-flight FTS Grounding)：
        探测智能体提炼的每个关键词在全量岗位库中的真实存在量，
        如果全库查无此词 (hit_count == 0)，则自动将其标注并禁用，
        保证最终进入推荐引擎的每个词汇都能 100% 击中真实岗位。
        """
        if isinstance(matrix, dict):
            categories = matrix.get("categories", {})
        else:
            categories = matrix.categories.dict() if hasattr(matrix.categories, "dict") else {}

        verified_categories = {
            "core": [],
            "domain": [],
            "base": [],
            "negative": []
        }
        zero_hit_keywords = []

        for cat_name in ["core", "domain", "base", "negative"]:
            items = categories.get(cat_name, [])
            for item in items:
                kw = item.get("keyword") if isinstance(item, dict) else getattr(item, "keyword", "")
                if not kw:
                    continue
                
                # 负向排斥词无需校验存在性（即使数据库没有也可作为过滤防御）
                if cat_name == "negative":
                    verified_categories[cat_name].append(item)
                    continue

                # 探测在全量数据库中的命中数
                hits = await self.job_repo.count_jobs_by_keyword(kw)
                
                # 探测并注册在 HITL 特征字典中的权重条目
                f_type = "domain" if cat_name == "domain" else "skill"
                f_key = f"{f_type}:{kw}"
                await self.user_repo.batch_register_feature_metadata([(f_key, f_type)])
                
                # 规范化对象
                item_dict = item if isinstance(item, dict) else item.dict()
                if hits == 0:
                    # 自动软禁用并提示
                    item_dict["enabled"] = False
                    orig_source = item_dict.get("source", "")
                    if "(全库0命中)" not in orig_source:
                        item_dict["source"] = f"{orig_source} [全库0命中,已自动禁用]".strip()
                    zero_hit_keywords.append(kw)
                else:
                    orig_source = item_dict.get("source", "")
                    if "(全库" not in orig_source:
                        item_dict["source"] = f"{orig_source} (全库{hits}岗对齐)".strip()
                
                verified_categories[cat_name].append(item_dict)

        result_matrix = {
            "version": 1,
            "updated_at": datetime.now().isoformat(),
            "updated_by": "GROUNDING_VERIFIED",
            "categories": verified_categories
        }
        return {
            "matrix": result_matrix,
            "zero_hit_keywords": zero_hit_keywords,
            "grounded": len(zero_hit_keywords) == 0
        }
