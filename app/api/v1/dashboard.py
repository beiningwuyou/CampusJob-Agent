from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import JobPosting, JobMatchAdvice, SourceConfig
from app.db.repositories.job_repo import JobRepository

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """获取仪表盘核心 KPI 汇总指标"""
    # 1. 统计总量
    total_jobs_res = await db.execute(select(func.count(JobPosting.id)))
    total_jobs = total_jobs_res.scalar() or 0

    # 2. 强烈推荐 (得分 >= 80)
    high_match_res = await db.execute(
        select(func.count(JobMatchAdvice.id)).where(JobMatchAdvice.match_score >= 80)
    )
    high_match_count = high_match_res.scalar() or 0

    # 3. 72 小时内紧急截止
    now = datetime.now()
    urgent_limit = now + timedelta(hours=72)
    urgent_res = await db.execute(
        select(func.count(JobPosting.id)).where(
            JobPosting.apply_ddl >= now,
            JobPosting.apply_ddl <= urgent_limit
        )
    )
    urgent_ddl_count = urgent_res.scalar() or 0

    # 4. 活跃信源数
    active_sources_res = await db.execute(
        select(func.count(SourceConfig.id)).where(SourceConfig.status == "ACTIVE")
    )
    active_sources_count = active_sources_res.scalar() or 0

    # 5. 今日 Top 推荐岗位
    job_repo = JobRepository(db)
    top_jobs, _ = await job_repo.list_jobs(min_score=75, limit=5)

    top_jobs_data = [{
        "id": j.id,
        "org_name": j.org_name,
        "job_title": j.job_title,
        "posting_type": j.posting_type,
        "work_locations": j.work_locations,
        "salary_desc": j.salary_desc,
        "score": j.advice.match_score if j.advice else 80,
        "match_level": j.advice.match_level if j.advice else "HIGH",
        "apply_ddl": j.apply_ddl,
    } for j in top_jobs]

    return {
        "metrics": {
            "total_jobs": total_jobs,
            "high_match_count": high_match_count,
            "urgent_ddl_count": urgent_ddl_count,
            "active_sources_count": active_sources_count
        },
        "top_recommended": top_jobs_data,
        "recent_trends": {
            "dates": [(now - timedelta(days=i)).strftime("%m-%d") for i in range(6, -1, -1)],
            "enterprise_counts": [5, 8, 12, 15, 14, 18, 20],
            "civil_counts": [2, 1, 3, 4, 2, 5, 4]
        }
    }
