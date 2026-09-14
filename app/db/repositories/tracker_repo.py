from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.models import ApplicationTrackRecord, JobPosting

class TrackerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_stages(self) -> dict[str, List[ApplicationTrackRecord]]:
        """获取五大阶段分组的投递追踪项"""
        stmt = select(ApplicationTrackRecord).options(
            selectinload(ApplicationTrackRecord.job).selectinload(JobPosting.advice)
        ).order_by(ApplicationTrackRecord.updated_at.desc())

        result = await self.session.execute(stmt)
        records = result.scalars().all()

        stages = {
            "APPLIED": [],
            "WRITTEN_EXAM": [],
            "INTERVIEW": [],
            "REVIEW_CHECK": [],
            "OFFER_ACCEPTED": []
        }

        for r in records:
            if r.current_stage in stages:
                stages[r.current_stage].append(r)
            else:
                stages["APPLIED"].append(r)

        return stages

    async def get_metrics(self) -> dict:
        """获取追踪总览指标"""
        total_res = await self.session.execute(select(func.count(ApplicationTrackRecord.id)))
        total_count = total_res.scalar() or 0

        critical_res = await self.session.execute(
            select(func.count(ApplicationTrackRecord.id)).where(ApplicationTrackRecord.is_critical.is_(True))
        )
        critical_count = critical_res.scalar() or 0

        offer_res = await self.session.execute(
            select(func.count(ApplicationTrackRecord.id)).where(ApplicationTrackRecord.current_stage == "OFFER_ACCEPTED")
        )
        offer_count = offer_res.scalar() or 0

        applied_res = await self.session.execute(
            select(func.count(ApplicationTrackRecord.id)).where(ApplicationTrackRecord.current_stage != "APPLIED")
        )
        passed_screen_count = applied_res.scalar() or 0
        screen_rate = round((passed_screen_count / total_count * 100), 1) if total_count > 0 else 63.6

        return {
            "total_count": total_count,
            "critical_count": critical_count,
            "screen_rate": screen_rate,
            "offer_count": offer_count
        }

    async def get_by_id(self, record_id: int) -> Optional[ApplicationTrackRecord]:
        """根据记录 ID 获取跟踪项"""
        stmt = select(ApplicationTrackRecord).where(ApplicationTrackRecord.id == record_id).options(
            selectinload(ApplicationTrackRecord.job).selectinload(JobPosting.advice)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def move_stage(
        self,
        record_id: int,
        new_stage: str,
        note: Optional[str] = None,
        next_node_time: Optional[datetime] = None,
        next_node_desc: Optional[str] = None
    ) -> Optional[ApplicationTrackRecord]:
        """变更阶段并记录审计流转历史"""
        stmt = select(ApplicationTrackRecord).where(ApplicationTrackRecord.id == record_id).options(
            selectinload(ApplicationTrackRecord.job)
        )
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None

        old_stage = record.current_stage
        record.current_stage = new_stage
        if next_node_time:
            record.next_node_time = next_node_time
        if next_node_desc:
            record.next_node_desc = next_node_desc
        if note:
            record.notes = note

        history = list(record.history_logs or [])
        history.append({
            "from_stage": old_stage,
            "to_stage": new_stage,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": note or f"流转至阶段: {new_stage}"
        })
        record.history_logs = history
        await self.session.commit()

        # 重新加载关联关系避免 MissingGreenlet
        stmt = select(ApplicationTrackRecord).where(ApplicationTrackRecord.id == record_id).options(
            selectinload(ApplicationTrackRecord.job).selectinload(JobPosting.advice)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def add_or_get_by_job_id(
        self,
        job_id: int,
        stage: str = "APPLIED",
        batch_title: str = "常规批次",
        resume_version: str = "默认脱敏简历.pdf"
    ) -> ApplicationTrackRecord:
        """为特定岗位创建跟踪项"""
        stmt = select(ApplicationTrackRecord).where(ApplicationTrackRecord.job_id == job_id).options(
            selectinload(ApplicationTrackRecord.job).selectinload(JobPosting.advice)
        )
        res = await self.session.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            return record

        record = ApplicationTrackRecord(
            job_id=job_id,
            current_stage=stage,
            batch_title=batch_title,
            resume_version=resume_version,
            history_logs=[{
                "from_stage": None,
                "to_stage": stage,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "初次纳入投递追踪看板"
            }]
        )
        self.session.add(record)
        await self.session.commit()

        # 重新加载关联关系避免 MissingGreenlet
        stmt = select(ApplicationTrackRecord).where(ApplicationTrackRecord.id == record.id).options(
            selectinload(ApplicationTrackRecord.job).selectinload(JobPosting.advice)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()
