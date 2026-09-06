import json
import aiosqlite
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Union
from src.models import ApplicationItem, ResumeItem, FeedbackRequest, KeywordMatrix
from src.db import get_user_db
from src.config import config

class UserDataRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    # --- Application Tracker ---
    async def create_or_update_application(self, app: ApplicationItem) -> bool:
        async with get_user_db(self.db_path) as db:
            await db.execute("""
            INSERT INTO applications (
                id, job_id, company, title, resume_id, status, apply_date,
                schedule_time, channel, account_memo, interview_notes, salary_offered,
                priority, match_score, recommend_reason, is_archived, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(id) DO UPDATE SET
                company=excluded.company,
                title=excluded.title,
                resume_id=excluded.resume_id,
                status=excluded.status,
                apply_date=excluded.apply_date,
                schedule_time=excluded.schedule_time,
                channel=excluded.channel,
                account_memo=excluded.account_memo,
                interview_notes=excluded.interview_notes,
                salary_offered=excluded.salary_offered,
                priority=excluded.priority,
                match_score=COALESCE(excluded.match_score, applications.match_score),
                recommend_reason=COALESCE(excluded.recommend_reason, applications.recommend_reason),
                is_archived=COALESCE(excluded.is_archived, applications.is_archived),
                updated_at=datetime('now', 'localtime')
            """, (
                app.id, app.job_id, app.company, app.title, app.resume_id,
                app.status, app.apply_date, app.schedule_time, app.channel,
                app.account_memo, app.interview_notes, app.salary_offered, app.priority,
                app.match_score, app.recommend_reason, 1 if app.is_archived else 0
            ))
            await db.commit()
            return True

    save_application = create_or_update_application

    async def list_applications(self, status: Optional[str] = None, include_archived: bool = True) -> List[ApplicationItem]:
        async with get_user_db(self.db_path) as db:
            conditions = []
            params = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if not include_archived:
                conditions.append("(is_archived = 0 OR is_archived IS NULL)")
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM applications {where_clause} ORDER BY priority DESC, updated_at DESC"
            
            async with db.execute(sql, tuple(params)) as cursor:
                rows = await cursor.fetchall()
                return [ApplicationItem(**{**dict(r), "is_archived": bool(dict(r).get("is_archived", 0))}) for r in rows]

    async def set_application_archived(self, app_id: str, is_archived: bool) -> bool:
        async with get_user_db(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE applications 
                SET is_archived = ?, updated_at = datetime('now', 'localtime') 
                WHERE id = ?
            """, (1 if is_archived else 0, app_id))
            await db.commit()
            return cursor.rowcount > 0

    async def delete_application(self, app_id: str) -> bool:
        async with get_user_db(self.db_path) as db:
            await db.execute("DELETE FROM application_timeline WHERE application_id = ?", (app_id,))
            cursor = await db.execute("DELETE FROM applications WHERE id = ?", (app_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def update_application_status(self, app_id: str, new_status: str, note: Optional[str] = None, schedule_time: Optional[str] = None) -> bool:
        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT status FROM applications WHERE id = ?", (app_id,)) as cursor:
                row = await cursor.fetchone()
                old_status = row["status"] if row else "UNKNOWN"

            if schedule_time:
                await db.execute("""
                    UPDATE applications 
                    SET status = ?, schedule_time = ?, updated_at = datetime('now', 'localtime') 
                    WHERE id = ?
                """, (new_status, schedule_time, app_id))
            else:
                await db.execute("""
                    UPDATE applications 
                    SET status = ?, updated_at = datetime('now', 'localtime') 
                    WHERE id = ?
                """, (new_status, app_id))

            import uuid
            tid = f"tl_{uuid.uuid4().hex[:8]}"
            await db.execute("""
                INSERT INTO application_timeline (id, application_id, from_status, to_status, note, changed_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (tid, app_id, old_status, new_status, note or f"状态变更为 {new_status}"))

            await db.commit()
            return True

    async def get_feature_weights(self) -> Dict[str, float]:
        return await self.get_all_feature_weights()


    # --- Resumes ---
    async def save_resume(self, resume: ResumeItem) -> bool:
        async with get_user_db(self.db_path) as db:
            if resume.is_default:
                await db.execute("UPDATE resumes SET is_default = 0")

            # 核心技术栈与画像技能统一：若提供了 parsed_skills 但无 keywords_matrix，自动构建 core 矩阵
            # 若提供了 keywords_matrix，确保 core 包含全部 parsed_skills
            matrix = resume.keywords_matrix
            skills = resume.parsed_skills or []
            if skills and not matrix:
                from src.models import KeywordCategories, KeywordItem
                core_items = [
                    KeywordItem(keyword=s.strip(), weight=1.5, source="简历画像核心技术栈", enabled=True)
                    for s in skills
                    if s and s.strip()
                ]
                matrix = KeywordMatrix(
                    version=1,
                    updated_at=datetime.utcnow().isoformat(),
                    updated_by="RESUME_PROFILE_SYNC",
                    categories=KeywordCategories(
                        core=core_items,
                        domain=[],
                        base=[],
                        negative=[]
                    )
                )
                resume.keywords_matrix = matrix
            elif matrix and hasattr(matrix, "categories") and matrix.categories:
                # 矩阵与 skills 保持同步
                core_list = [k.keyword.strip() for k in (matrix.categories.core or []) if k and k.keyword]
                if core_list:
                    skills = core_list
                    resume.parsed_skills = skills

            matrix_json = None
            if resume.keywords_matrix:
                matrix_json = resume.keywords_matrix.model_dump_json() if hasattr(resume.keywords_matrix, "model_dump_json") else json.dumps(resume.keywords_matrix, ensure_ascii=False)
            await db.execute("""
            INSERT INTO resumes (
                id, title, category, file_path, content_md, target_job_id,
                parsed_skills, keywords_matrix, is_default, version_type, parent_resume_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                category=excluded.category,
                file_path=excluded.file_path,
                content_md=excluded.content_md,
                target_job_id=excluded.target_job_id,
                parsed_skills=excluded.parsed_skills,
                keywords_matrix=excluded.keywords_matrix,
                is_default=excluded.is_default,
                version_type=excluded.version_type,
                parent_resume_id=excluded.parent_resume_id,
                updated_at=datetime('now', 'localtime')
            """, (
                resume.id, resume.title, resume.category, resume.file_path,
                resume.content_md, resume.target_job_id,
                json.dumps(resume.parsed_skills, ensure_ascii=False) if resume.parsed_skills else "[]",
                matrix_json,
                1 if resume.is_default else 0,
                getattr(resume, "version_type", "ORIGINAL"),
                getattr(resume, "parent_resume_id", None)
            ))
            await db.commit()

            # 自动注册矩阵技能到 HITL 特征字典 (保证 100% 包含与约束)
            if resume.keywords_matrix:
                await self.auto_register_matrix_features(resume.keywords_matrix)

            return True

    async def set_default_resume(self, resume_id: str) -> bool:
        async with get_user_db(self.db_path) as db:
            await db.execute("UPDATE resumes SET is_default = 0")
            cursor = await db.execute("UPDATE resumes SET is_default = 1, updated_at = datetime('now', 'localtime') WHERE id = ?", (resume_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def list_resumes(self) -> List[ResumeItem]:
        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT * FROM resumes ORDER BY is_default DESC, updated_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_resume(r) for r in rows]

    async def get_resume_by_id(self, resume_id: str) -> Optional[ResumeItem]:
        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)) as cursor:
                r = await cursor.fetchone()
                if not r:
                    return None
                return self._row_to_resume(r)

    # Alias for compatibility with tests
    get_resume = get_resume_by_id

    async def init_db(self):
        from src.db import init_user_db
        await init_user_db(self.db_path)

    async def update_resume(
        self,
        resume_id: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        content_md: Optional[str] = None,
        skills: Optional[List[str]] = None,
        keywords_matrix: Optional[Union[KeywordMatrix, dict]] = None,
        is_default: Optional[bool] = None,
        version_type: Optional[str] = None,
        parent_resume_id: Optional[str] = None
    ) -> Optional[ResumeItem]:
        async with get_user_db(self.db_path) as db:
            if is_default:
                await db.execute("UPDATE resumes SET is_default = 0")

            # 核心技术栈与画像技能统一
            # 1. 若同时或仅传入 skills，同步更新或补齐 keywords_matrix 的 core 象限
            if skills is not None and keywords_matrix is None:
                # 获取原简历已有的矩阵进行合并，若无则新建
                async with db.execute("SELECT keywords_matrix FROM resumes WHERE id = ?", (resume_id,)) as cur:
                    row = await cur.fetchone()
                    existing_matrix_str = row[0] if row else None
                existing_matrix = None
                if existing_matrix_str:
                    try:
                        m_dict = json.loads(existing_matrix_str)
                        if m_dict:
                            existing_matrix = KeywordMatrix(**m_dict)
                    except Exception:
                        pass
                
                from src.models import KeywordCategories, KeywordItem
                core_items = [
                    KeywordItem(keyword=s.strip(), weight=1.5, source="简历画像核心技术栈", enabled=True)
                    for s in skills
                    if s and s.strip()
                ]
                if existing_matrix and existing_matrix.categories:
                    existing_matrix.categories.core = core_items
                    existing_matrix.updated_at = datetime.utcnow().isoformat()
                    existing_matrix.updated_by = "RESUME_SKILLS_UPDATE"
                    keywords_matrix = existing_matrix
                else:
                    keywords_matrix = KeywordMatrix(
                        version=1,
                        updated_at=datetime.utcnow().isoformat(),
                        updated_by="RESUME_SKILLS_UPDATE",
                        categories=KeywordCategories(core=core_items, domain=[], base=[], negative=[])
                    )
            elif keywords_matrix is not None:
                # 若传入了 keywords_matrix，反向同步 skills 为 core 的关键词列表
                matrix_obj = keywords_matrix if isinstance(keywords_matrix, KeywordMatrix) else KeywordMatrix(**keywords_matrix)
                if matrix_obj.categories and matrix_obj.categories.core is not None:
                    skills = [item.keyword.strip() for item in matrix_obj.categories.core if item and item.keyword]
            
            updates = []
            params = []
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if category is not None:
                updates.append("category = ?")
                params.append(category)
            if content_md is not None:
                updates.append("content_md = ?")
                params.append(content_md)
            if skills is not None:
                updates.append("parsed_skills = ?")
                params.append(json.dumps(skills, ensure_ascii=False))
            if keywords_matrix is not None:
                updates.append("keywords_matrix = ?")
                matrix_str = keywords_matrix.model_dump_json() if hasattr(keywords_matrix, "model_dump_json") else json.dumps(keywords_matrix, ensure_ascii=False)
                params.append(matrix_str)
            if is_default is not None:
                updates.append("is_default = ?")
                params.append(1 if is_default else 0)
            if version_type is not None:
                updates.append("version_type = ?")
                params.append(version_type)
            if parent_resume_id is not None:
                updates.append("parent_resume_id = ?")
                params.append(parent_resume_id)
            
            updates.append("updated_at = datetime('now', 'localtime')")
            params.append(resume_id)
            
            query = f"UPDATE resumes SET {', '.join(updates)} WHERE id = ?"
            cursor = await db.execute(query, tuple(params))
            await db.commit()
            if cursor.rowcount == 0:
                return None

            # 自动注册矩阵技能到 HITL 特征字典 (保证 100% 包含与约束)
            if keywords_matrix:
                await self.auto_register_matrix_features(keywords_matrix)

            return await self.get_resume_by_id(resume_id)

    async def update_resume_keywords_matrix(
        self,
        resume_id: str,
        keywords_matrix: Union[KeywordMatrix, dict]
    ) -> Optional[ResumeItem]:
        return await self.update_resume(resume_id=resume_id, keywords_matrix=keywords_matrix)

    async def delete_resume(self, resume_id: str) -> bool:
        async with get_user_db(self.db_path) as db:
            cursor = await db.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            await db.commit()
            return cursor.rowcount > 0

    def _row_to_resume(self, r: Any) -> ResumeItem:
        skills = []
        if r["parsed_skills"]:
            try:
                skills = json.loads(r["parsed_skills"])
            except:
                pass
        matrix = None
        if "keywords_matrix" in r.keys() and r["keywords_matrix"]:
            try:
                m_data = json.loads(r["keywords_matrix"])
                if m_data:
                    matrix = KeywordMatrix(**m_data)
            except:
                pass

        # 核心技术栈与画像技能统一：若已有 keywords_matrix，画像技能以 core 核心技术栈为准
        if matrix and matrix.categories and matrix.categories.core is not None:
            core_keywords = [
                item.keyword.strip()
                for item in matrix.categories.core
                if item and item.keyword and item.keyword.strip()
            ]
            if core_keywords:
                skills = core_keywords
        elif skills and not matrix:
            # 若已有 skills 但未建立 keywords_matrix，自动缺省投影生成初始 core 矩阵
            from src.models import KeywordCategories, KeywordItem
            core_items = [
                KeywordItem(keyword=s.strip(), weight=1.5, source="简历画像核心技术栈", enabled=True)
                for s in skills
                if s and s.strip()
            ]
            matrix = KeywordMatrix(
                version=1,
                updated_at=datetime.utcnow().isoformat(),
                updated_by="RESUME_PROFILE_SYNC",
                categories=KeywordCategories(
                    core=core_items,
                    domain=[],
                    base=[],
                    negative=[]
                )
            )

        is_def = bool(r["is_default"]) if "is_default" in r.keys() else False
        v_type = r["version_type"] if "version_type" in r.keys() and r["version_type"] else "ORIGINAL"
        p_id = r["parent_resume_id"] if "parent_resume_id" in r.keys() else None
        return ResumeItem(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            file_path=r["file_path"],
            content_md=r["content_md"],
            target_job_id=r["target_job_id"],
            parsed_skills=skills,
            keywords_matrix=matrix,
            is_default=is_def,
            version_type=v_type,
            parent_resume_id=p_id,
            created_at=r["created_at"],
            updated_at=r["updated_at"]
        )

    async def get_default_resume(self) -> Optional[ResumeItem]:
        """Fetch the default active resume. If no default is set, fallback to the latest resume."""
        async with get_user_db(self.db_path) as db:
            # First try to find is_default = 1
            async with db.execute("SELECT * FROM resumes WHERE is_default = 1 LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_resume(row)
            # Fallback to the latest updated resume
            async with db.execute("SELECT * FROM resumes ORDER BY updated_at DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_resume(row)
        return None

    get_resume = get_resume_by_id

    # --- HITL Recommendation & Feature Weights ---
    async def record_feedback(
        self,
        feedback: FeedbackRequest,
        job_company: str,
        job_tags: List[str],
        job_industry: Optional[str],
        job_categories: Optional[List[str]] = None,
        job_city: Optional[str] = None
    ) -> bool:
        async with get_user_db(self.db_path) as db:
            import uuid
            fid = f"fb_{uuid.uuid4().hex[:8]}"
            await db.execute("""
            INSERT INTO recommendation_feedback (
                id, job_id, match_score, recommend_reason, action, reject_reasons
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                fid, feedback.job_id, feedback.match_score, feedback.recommend_reason,
                feedback.action, json.dumps(feedback.reject_reasons, ensure_ascii=False) if feedback.reject_reasons else "[]"
            ))

            # Update feature weights
            is_accept = (feedback.action == "ACCEPT")
            reject_reasons = feedback.reject_reasons or []

            # P0: 拒绝原因定向衰减（拒绝什么扣什么，杜绝连坐误伤）
            # 若用户明确选择了原因，则精准识别目标维度并执行定向衰减：
            target_category = False
            target_industry = False
            target_city = False

            if not is_accept and reject_reasons:
                reasons_text = " ".join(reject_reasons).lower()
                # 职能/方向关键词 (前端传输 'direction' 或含有相关中文)
                if any(k in reasons_text for k in ["direction", "类型", "职能", "岗位", "category", "职位", "专业", "研发", "算法"]):
                    target_category = True
                # 垂直行业/赛道关键词 (前端传输 'industry' 或相关中文)
                if any(k in reasons_text for k in ["industry", "行业", "赛道", "金融", "地产", "外包"]):
                    target_industry = True
                # 城市/地理位置关键词 (前端传输 'location' 或相关中文)
                if any(k in reasons_text for k in ["location", "city", "地点", "城市", "地区", "太远", "不去"]):
                    target_city = True
                
                # 如果用户填写的自定义原因没有命中上述关键词，则默认温和衰减所有涉及特征
                if not (target_category or target_industry or target_city):
                    target_category = target_industry = target_city = True
            else:
                # 接受操作，或未指定原因的纯快速拒绝：涉及的维度均参与更新
                target_category = target_industry = target_city = True

            # 1. 岗位类型维度 (category) - 核心职能偏好
            if is_accept or target_category:
                # 若为无原因快速拒绝，衰减幅度温和（0.85x）；若针对性指认，力度为 0.75x
                decay_rate = 0.75 if (not is_accept and target_category and reject_reasons) else 0.85
                for cat in (job_categories or []):
                    cat_key = f"category:{cat}"
                    await self._adjust_feature_weight(db, cat_key, "category", is_accept, decay_rate=decay_rate)

            # 2. 垂直行业维度 (industry)
            if (is_accept or target_industry) and job_industry and job_industry not in ["综合", "其他", "科技"]:
                decay_rate = 0.75 if (not is_accept and target_industry and reject_reasons) else 0.85
                ind_key = f"industry:{job_industry}"
                await self._adjust_feature_weight(db, ind_key, "industry", is_accept, decay_rate=decay_rate)

            # 3. 期望城市地域 (city)
            if (is_accept or target_city) and job_city:
                decay_rate = 0.75 if (not is_accept and target_city and reject_reasons) else 0.85
                city_key = f"city:{job_city}"
                await self._adjust_feature_weight(db, city_key, "city", is_accept, decay_rate=decay_rate)

            await db.commit()
            return True

    async def _adjust_feature_weight(
        self,
        db: aiosqlite.Connection,
        feature_key: str,
        feature_type: str,
        is_accept: bool,
        decay_rate: float = 0.75
    ):
        async with db.execute("SELECT weight, accept_count, reject_count FROM feature_weights WHERE feature_key = ?", (feature_key,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                current_weight = 1.0
                accept_count = 0
                reject_count = 0
            else:
                current_weight = row["weight"]
                accept_count = row["accept_count"]
                reject_count = row["reject_count"]

        if is_accept:
            # 边际递减奖励 (上限 2.0)
            new_weight = min(config.max_weight_ceiling, current_weight + config.accept_reward * (1.0 + (1.0 - current_weight/2.0)))
            accept_count += 1
        else:
            # 温和惩罚 (下限 0.10, 衰减 decay_rate)
            new_weight = max(config.min_weight_floor, current_weight * decay_rate)
            reject_count += 1

        await db.execute("""
        INSERT INTO feature_weights (feature_key, feature_type, weight, accept_count, reject_count, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
        ON CONFLICT(feature_key) DO UPDATE SET
            weight=excluded.weight,
            accept_count=excluded.accept_count,
            reject_count=excluded.reject_count,
            updated_at=datetime('now', 'localtime')
        """, (feature_key, feature_type, round(new_weight, 4), accept_count, reject_count))

    async def list_feedback(self) -> List[Dict[str, Any]]:
        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT * FROM recommendation_feedback ORDER BY feedback_time DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_feature_weights(self) -> Dict[str, float]:
        return await self.get_all_feature_weights()

    async def get_all_feature_weights(self) -> Dict[str, float]:
        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT feature_key, weight FROM feature_weights") as cursor:
                rows = await cursor.fetchall()
                return {r["feature_key"]: r["weight"] for r in rows}

    async def get_detailed_feature_weights(self) -> List[Dict[str, Any]]:
        async with get_user_db(self.db_path) as db:
            async with db.execute("""
                SELECT feature_key, feature_type, weight, accept_count, reject_count, updated_at 
                FROM feature_weights 
                ORDER BY updated_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def batch_register_feature_metadata(self, features: List[Tuple[str, str]]) -> int:
        """
        轻量级增量注册特征元数据（若不存在则写入默认权重 1.0，用于爬虫/MCP特征字典对齐）
        features: [(feature_key, feature_type)]
        返回新增注册的特征数
        """
        if not features:
            return 0
        async with get_user_db(self.db_path) as db:
            # 使用 INSERT OR IGNORE 与 executemany 进行批量高效注册
            params = [(f_key, f_type) for f_key, f_type in features]
            cursor = await db.executemany("""
                INSERT OR IGNORE INTO feature_weights (feature_key, feature_type, weight, accept_count, reject_count, updated_at)
                VALUES (?, ?, 1.0, 0, 0, CURRENT_TIMESTAMP)
            """, params)
            await db.commit()
            return cursor.rowcount if cursor.rowcount > 0 else 0

    async def auto_register_matrix_features(self, matrix: Union[KeywordMatrix, dict]) -> int:
        """
        自动将推荐语义关键词矩阵中的关键词注册到 HITL feature_weights 表，
        支持 core/domain/base -> skill / domain 命名空间，保证 100% 包含与约束。
        """
        if not matrix:
            return 0
        if isinstance(matrix, dict):
            cats_dict = matrix.get("categories") or {}
            if hasattr(cats_dict, "dict"):
                cats_dict = cats_dict.dict()
        elif hasattr(matrix, "categories"):
            cats_obj = matrix.categories
            cats_dict = cats_obj.dict() if hasattr(cats_obj, "dict") else vars(cats_obj)
        else:
            cats_dict = {}

        features_to_sync = []
        for cat_name, items in cats_dict.items():
            f_type = "domain" if cat_name == "domain" else "skill"
            if isinstance(items, list):
                for it in items:
                    kw = it.keyword if hasattr(it, "keyword") else (it.get("keyword") if isinstance(it, dict) else str(it))
                    if kw and str(kw).strip():
                        clean_kw = str(kw).strip()
                        features_to_sync.append((f"{f_type}:{clean_kw}", f_type))

        if features_to_sync:
            return await self.batch_register_feature_metadata(features_to_sync)
        return 0

    async def reset_feature_weights(self, feature_key: Optional[str] = None) -> bool:
        """
        将权重恢复至 1.0 基准线，同时重置 accept_count 和 reject_count 计数，
        保留特征元数据本身，彻底避免清空字典。
        """
        async with get_user_db(self.db_path) as db:
            if feature_key:
                await db.execute("""
                    UPDATE feature_weights 
                    SET weight = 1.0, accept_count = 0, reject_count = 0, updated_at = datetime('now', 'localtime')
                    WHERE feature_key = ?
                """, (feature_key,))
            else:
                await db.execute("""
                    UPDATE feature_weights 
                    SET weight = 1.0, accept_count = 0, reject_count = 0, updated_at = datetime('now', 'localtime')
                """)
            await db.commit()
            return True

    # ------------------ Agent Push (AI智能体主动特推) ------------------
    async def add_agent_push(self, job_id: str, recommend_reason: str, match_score: float = 0.95, agent_name: str = "JobSourcingAgent") -> str:
        """记录智能体主动推送的精选岗位卡片"""
        import uuid
        push_id = str(uuid.uuid4())
        async with get_user_db(self.db_path) as db:
            await db.execute("""
                INSERT INTO agent_pushes (id, job_id, agent_name, recommend_reason, match_score, pushed_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (push_id, job_id, agent_name, recommend_reason, match_score))
            await db.commit()
        return push_id

    async def list_agent_pushes(self) -> List[Dict[str, Any]]:
        """获取所有未被用户直接交互/处理的智能体特推列表"""
        async with get_user_db(self.db_path) as db:
            async with db.execute("""
                SELECT p.* FROM agent_pushes p
                LEFT JOIN recommendation_feedback f ON p.job_id = f.job_id
                WHERE f.job_id IS NULL
                ORDER BY p.pushed_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def dismiss_agent_push(self, push_id: str) -> bool:
        """移除指定智能体特推记录"""
        async with get_user_db(self.db_path) as db:
            await db.execute("DELETE FROM agent_pushes WHERE id = ?", (push_id,))
            await db.commit()
            return True

    async def get_company_application_status(self, max_pending_limit: int = 3) -> Dict[str, Any]:
        """
        获取企业层级的投递状态统计与频控信息：
        - applied_companies: set of str, 已经正式投递过的企业（状态不为 PENDING_APPLY 的所有申请）
        - pending_counts: dict of {company: int}, 处于待投递 (PENDING_APPLY) 状态的岗位数
        - capped_pending_companies: set of str, 待投递岗位已 >= max_pending_limit 的企业（触发频控上限）
        """
        from collections import Counter
        applied_companies = set()
        pending_counts = Counter()

        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT company, status FROM applications") as cursor:
                rows = await cursor.fetchall()
                for r in rows:
                    comp = (r["company"] or "").strip()
                    if not comp:
                        continue
                    status = (r["status"] or "").strip()
                    if status and status != "PENDING_APPLY":
                        applied_companies.add(comp)
                    elif status == "PENDING_APPLY":
                        pending_counts[comp] += 1

        capped_pending_companies = {comp for comp, cnt in pending_counts.items() if cnt >= max_pending_limit}
        return {
            "applied_companies": applied_companies,
            "pending_counts": dict(pending_counts),
            "pending_company_counts": dict(pending_counts),
            "capped_pending_companies": capped_pending_companies
        }

    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取用户系统设置"""
        async with get_user_db(self.db_path) as db:
            async with db.execute("SELECT setting_value FROM user_settings WHERE setting_key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                if row and row["setting_value"] is not None:
                    return str(row["setting_value"])
        return default

    async def set_setting(self, key: str, value: str) -> None:
        """保存用户系统设置"""
        async with get_user_db(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_settings (setting_key, setting_value, updated_at)
                VALUES (?, ?, datetime('now', 'localtime'))
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    updated_at = excluded.updated_at
                """,
                (key, value)
            )
            await db.commit()


# Alias
UserRepository = UserDataRepository


