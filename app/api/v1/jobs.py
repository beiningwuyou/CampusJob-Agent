from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.job_repo import JobRepository
from app.schemas.advice import JobListItemResponse, JobDetailResponse

router = APIRouter(prefix="/jobs", tags=["岗位与招考"])

@router.get("", response_model=dict)
async def list_jobs(
    posting_type: Optional[str] = Query(default=None, description="ENTERPRISE / CIVIL_EXAM / ALL"),
    min_score: int = Query(default=0, ge=0, le=100, description="最低匹配得分"),
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
    is_fresh_only: Optional[bool] = Query(default=None, description="是否限应届生"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """分页筛选全域岗位与招考流"""
    repo = JobRepository(db)
    items, total = await repo.list_jobs(
        posting_type=posting_type,
        min_score=min_score,
        keyword=keyword,
        is_fresh_only=is_fresh_only,
        limit=limit,
        offset=offset
    )

    items_data = []
    for item in items:
        resp = JobListItemResponse.model_validate(item)
        items_data.append(resp)

    return {
        "items": items_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取岗位详情与 AI 契合度/资格自查报告"""
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位或招考信息不存在")
    return JobDetailResponse.model_validate(job)

@router.post("/{job_id}/apply")
async def toggle_applied_status(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """切换已投递/已报名状态"""
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    job.is_applied = not job.is_applied
    await db.commit()
    return {"id": job.id, "is_applied": job.is_applied}

@router.post("/{job_id}/track")
async def track_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """一键将该岗位加入投递追踪看板"""
    from app.db.repositories.tracker_repo import TrackerRepository
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    tracker_repo = TrackerRepository(db)
    rec = await tracker_repo.add_or_get_by_job_id(
        job_id=job.id,
        stage="APPLIED",
        batch_title="秋招提前批/招考常规批",
        resume_version="v4.2_分布式重构.pdf"
    )
    return {
        "status": "success",
        "message": f"已将【{job.org_name} - {job.job_title}】设为报考与投递追踪",
        "tracker_id": rec.id
    }

