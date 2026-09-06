import json
import aiosqlite
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
from src.models import JobItem, JobSearchQuery
from src.db import get_public_db

class JobRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    async def upsert_job(self, job: JobItem) -> bool:
        async with get_public_db(self.db_path) as db:
            await db.execute("""
            INSERT INTO jobs (
                id, title, company, location, industry, type_tags, batch,
                education_req, target_grad_year, salary_range, publish_date,
                deadline, detail_url, referral_code, description, source_site,
                popular_level, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                industry=excluded.industry,
                type_tags=excluded.type_tags,
                batch=excluded.batch,
                education_req=excluded.education_req,
                target_grad_year=excluded.target_grad_year,
                salary_range=excluded.salary_range,
                publish_date=excluded.publish_date,
                deadline=excluded.deadline,
                detail_url=excluded.detail_url,
                referral_code=excluded.referral_code,
                description=excluded.description,
                source_site=excluded.source_site,
                popular_level=excluded.popular_level,
                updated_at=datetime('now', 'localtime')
            """, (
                job.id, job.title, job.company, job.location, job.industry,
                json.dumps(job.type_tags, ensure_ascii=False), job.batch,
                job.education_req, json.dumps(job.target_grad_year or [], ensure_ascii=False),
                job.salary_range, job.publish_date, job.deadline, job.detail_url,
                job.referral_code, job.description, job.source_site, job.popular_level
            ))
            # Sync FTS
            await db.execute("""
            INSERT OR REPLACE INTO jobs_fts(rowid, title, company, location, description)
            VALUES ((SELECT rowid FROM jobs WHERE id = ?), ?, ?, ?, ?)
            """, (job.id, job.title, job.company, job.location or "", job.description or ""))
            await db.commit()
            return True

    insert_job = upsert_job


    async def batch_upsert(self, jobs: List[JobItem]) -> int:
        if not jobs:
            return 0
        async with get_public_db(self.db_path) as db:
            await db.execute("PRAGMA synchronous = NORMAL;")
            insert_job_sql = """
            INSERT INTO jobs (
                id, title, company, location, industry, type_tags, batch,
                education_req, target_grad_year, salary_range, publish_date,
                deadline, detail_url, referral_code, description, source_site, popular_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                industry=excluded.industry,
                type_tags=excluded.type_tags,
                batch=excluded.batch,
                education_req=excluded.education_req,
                target_grad_year=excluded.target_grad_year,
                salary_range=excluded.salary_range,
                publish_date=excluded.publish_date,
                deadline=excluded.deadline,
                detail_url=excluded.detail_url,
                referral_code=excluded.referral_code,
                description=excluded.description,
                source_site=excluded.source_site,
                popular_level=excluded.popular_level,
                updated_at=datetime('now', 'localtime')
            """
            job_rows = [
                (
                    job.id, job.title, job.company, job.location, job.industry,
                    json.dumps(job.type_tags, ensure_ascii=False) if isinstance(job.type_tags, list) else job.type_tags,
                    job.batch,
                    job.education_req,
                    json.dumps(job.target_grad_year or [], ensure_ascii=False) if isinstance(job.target_grad_year, list) else job.target_grad_year,
                    job.salary_range, job.publish_date, job.deadline, job.detail_url,
                    job.referral_code, job.description, job.source_site, job.popular_level
                )
                for job in jobs
            ]
            await db.executemany(insert_job_sql, job_rows)

            fts_sql = """
            INSERT OR REPLACE INTO jobs_fts(rowid, title, company, location, description)
            VALUES ((SELECT rowid FROM jobs WHERE id = ?), ?, ?, ?, ?)
            """
            fts_rows = [
                (job.id, job.title, job.company, job.location or "", job.description or "")
                for job in jobs
            ]
            await db.executemany(fts_sql, fts_rows)
            await db.commit()
            return len(jobs)

    upsert_jobs = batch_upsert

    async def record_sync_log(self, source_site: str, category: str, items_fetched: int,
                              items_inserted: int, items_updated: int, status: str, error_message: Optional[str] = None):
        import uuid
        log_id = f"sync_{uuid.uuid4().hex[:12]}"
        async with get_public_db(self.db_path) as db:
            await db.execute("""
            INSERT INTO sync_logs (
                id, source_site, category, items_fetched, items_inserted,
                items_updated, status, error_message, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (log_id, source_site, category, items_fetched, items_inserted, items_updated, status, error_message))
            await db.commit()
            return log_id

    async def get_job_by_id(self, job_id: str) -> Optional[JobItem]:
        jobs = await self.get_jobs_by_ids([job_id])
        return jobs.get(job_id)

    get_job = get_job_by_id

    async def get_jobs_by_ids(self, job_ids: List[str]) -> Dict[str, JobItem]:
        if not job_ids:
            return {}
        unique_ids = list(set(job_ids))
        res: Dict[str, JobItem] = {}
        # SQLite 变量上限保护，分批查询（每批 500 个）
        async with get_public_db(self.db_path) as db:
            for i in range(0, len(unique_ids), 500):
                chunk = unique_ids[i:i + 500]
                placeholders = ",".join("?" for _ in chunk)
                query = f"SELECT * FROM jobs WHERE id IN ({placeholders})"
                async with db.execute(query, chunk) as cursor:
                    rows = await cursor.fetchall()
                    for r in rows:
                        job = self._row_to_job(r)
                        res[job.id] = job
        return res

    async def find_job_by_company_and_title(self, company: str, title: str) -> Optional[JobItem]:
        """根据企业名称和岗位名称模糊补全岗位详情与链接（单次快速联合匹配，避免全表多次扫描）"""
        async with get_public_db(self.db_path) as db:
            clean_title = title.split('（')[0].split('(')[0].split('【')[0].strip()
            clean_co = (company.replace('股份有限公司', '')
                               .replace('有限责任公司', '')
                               .replace('科技', '')
                               .replace('集团', '')
                               .replace('有限', '')
                               .replace('公司', '')
                               .strip())
            
            # 单次高效企业或标题匹配
            async with db.execute(
                "SELECT * FROM jobs WHERE company LIKE ? OR title LIKE ? LIMIT 1",
                (f"%{clean_co[:4]}%", f"%{clean_title[:6]}%")
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_job(row)

            return None

    async def search_jobs(self, query: Optional[JobSearchQuery] = None, **kwargs) -> Tuple[List[JobItem], int]:
        if query is None:
            query = JobSearchQuery(**kwargs)
        conditions = []
        params = []

        # Time constraint resolution
        if query.since_date:
            conditions.append("publish_date >= ?")
            params.append(query.since_date)
        elif query.start_date and query.end_date:
            conditions.append("publish_date BETWEEN ? AND ?")
            params.extend([query.start_date, query.end_date])
        elif query.time_window_months:
            cutoff = (datetime.now() - timedelta(days=query.time_window_months * 30)).strftime("%Y-%m-%d")
            conditions.append("publish_date >= ?")
            params.append(cutoff)

        if query.company:
            conditions.append("company LIKE ?")
            params.append(f"%{query.company}%")

        if query.city:
            if query.city in ("海外", "境外", "海外/国际"):
                conditions.append("(location LIKE '%海外%' OR location LIKE '%香港%' OR location LIKE '%澳门%' OR location LIKE '%台湾%' OR location LIKE '%新加坡%' OR location LIKE '%美国%' OR location LIKE '%英国%' OR location LIKE '%日本%' OR location LIKE '%欧洲%' OR location LIKE '%澳大利亚%' OR location LIKE '%德国%')")
            elif query.city in ("远程/不限", "远程", "全国"):
                conditions.append("(location LIKE '%远程%' OR location LIKE '%居家%' OR location LIKE '%全国%' OR location LIKE '%不限%' OR location LIKE '%多城市%')")
            else:
                # 精准匹配工作地点 location 字段，避免仅在长篇 JD 推荐语中提及其他城市被误召回
                conditions.append("location LIKE ?")
                params.append(f"%{query.city}%")
        elif query.location:
            conditions.append("location LIKE ?")
            params.append(f"%{query.location}%")

        if query.batch:
            conditions.append("batch LIKE ?")
            params.append(f"%{query.batch}%")

        if query.has_referral is True:
            conditions.append("referral_code IS NOT NULL AND referral_code != ''")

        if query.category:
            if query.category == "campus":
                conditions.append("(batch LIKE '%校招%' OR batch LIKE '%秋招%' OR batch LIKE '%春招%' OR batch LIKE '%届%' OR type_tags LIKE '%校招%' OR title LIKE '%校招%')")
            elif query.category == "state_owned":
                conditions.append("(industry LIKE '%国企%' OR industry LIKE '%央企%' OR type_tags LIKE '%国企%' OR company LIKE '%中国%' OR company LIKE '%集团%')")
            elif query.category == "intern":
                conditions.append("(title LIKE '%实习%' OR batch LIKE '%实习%' OR type_tags LIKE '%实习%')")
            elif query.category == "returnee":
                conditions.append("(description LIKE '%留学生%' OR description LIKE '%海外%' OR description LIKE '%QS%' OR location LIKE '%海外%')")
            elif query.category == "latest":
                # Latest defaults to no special tag restriction, sorted by publish_date
                pass

        if query.education_req:
            conditions.append("education_req = ?")
            params.append(query.education_req)

        if query.keyword:
            conditions.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
            kw = f"%{query.keyword}%"
            params.extend([kw, kw, kw])

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        count_sql = f"SELECT COUNT(*) FROM jobs {where_clause}"
        select_sql = f"SELECT * FROM jobs {where_clause} ORDER BY publish_date DESC, popular_level DESC LIMIT ? OFFSET ?"
        
        async with get_public_db(self.db_path) as db:
            async with db.execute(count_sql, params) as cursor:
                total_row = await cursor.fetchone()
                total = total_row[0] if total_row else 0

            fetch_params = list(params) + [query.limit, query.offset]
            async with db.execute(select_sql, fetch_params) as cursor:
                rows = await cursor.fetchall()
                jobs = [self._row_to_job(r) for r in rows]

            return jobs, total

    def _row_to_job(self, row: aiosqlite.Row) -> JobItem:
        type_tags = []
        if row["type_tags"]:
            try:
                type_tags = json.loads(row["type_tags"])
            except:
                type_tags = [row["type_tags"]]

        target_grad_year = []
        if row["target_grad_year"]:
            try:
                target_grad_year = json.loads(row["target_grad_year"])
            except:
                target_grad_year = [row["target_grad_year"]]

        return JobItem(
            id=row["id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            industry=row["industry"],
            type_tags=type_tags,
            batch=row["batch"],
            education_req=row["education_req"],
            target_grad_year=target_grad_year,
            salary_range=row["salary_range"],
            publish_date=row["publish_date"],
            deadline=row["deadline"],
            detail_url=row["detail_url"],
            referral_code=row["referral_code"],
            description=row["description"],
            source_site=row["source_site"] or "default",
            popular_level=row["popular_level"] or 1,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
