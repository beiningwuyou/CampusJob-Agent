from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import JobPosting, JobMatchAdvice

class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_jobs(
        self,
        posting_type: Optional[str] = None,
        min_score: int = 0,
        city: Optional[str] = None,
        keyword: Optional[str] = None,
        is_fresh_only: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[JobPosting], int]:
        query = select(JobPosting).options(selectinload(JobPosting.advice)).where(JobPosting.is_archived.is_(False))

        if posting_type and posting_type != "ALL":
            query = query.where(JobPosting.posting_type == posting_type)

        if is_fresh_only is not None and is_fresh_only:
            query = query.where(JobPosting.is_fresh_only.is_(True))

        if keyword:
            kw = f"%{keyword.strip()}%"
            query = query.where(or_(
                JobPosting.org_name.ilike(kw),
                JobPosting.job_title.ilike(kw),
                JobPosting.category.ilike(kw)
            ))

        # 排序：联合 advice 的 match_score 降序，再按发布时间降序
        query = query.outerjoin(JobMatchAdvice, JobPosting.id == JobMatchAdvice.job_id)
        if min_score > 0:
            query = query.where(JobMatchAdvice.match_score >= min_score)

        query = query.order_by(desc(JobMatchAdvice.match_score), desc(JobPosting.created_at))

        # 执行查询
        paginated_query = query.limit(limit).offset(offset)
        res = await self.session.execute(paginated_query)
        jobs = list(res.scalars().all())

        return jobs, len(jobs)

    async def get_by_id(self, job_id: int) -> Optional[JobPosting]:
        stmt = (
            select(JobPosting)
            .options(selectinload(JobPosting.advice))
            .where(JobPosting.id == job_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def save_job_with_advice(
        self,
        job_data: dict,
        advice_data: dict
    ) -> JobPosting:
        job = JobPosting(**job_data)
        self.session.add(job)
        await self.session.flush()

        advice = JobMatchAdvice(
            job_id=job.id,
            posting_type=job.posting_type,
            **advice_data
        )
        self.session.add(advice)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_calendar_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[JobPosting]:
        """获取落在指定日期范围内的宣讲会、截止日或笔试日程"""
        stmt = (
            select(JobPosting)
            .options(selectinload(JobPosting.advice))
            .where(
                or_(
                    and_(JobPosting.talk_time >= start_date, JobPosting.talk_time <= end_date),
                    and_(JobPosting.apply_ddl >= start_date, JobPosting.apply_ddl <= end_date),
                    and_(JobPosting.exam_time >= start_date, JobPosting.exam_time <= end_date),
                    and_(JobPosting.apply_start >= start_date, JobPosting.apply_start <= end_date),
                )
            )
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
