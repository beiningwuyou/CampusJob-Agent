from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.matching_agent import MatchingAgent
from app.db.models import JobPosting, JobMatchAdvice, UserPreferenceProfile

async def reevaluate_all_jobs_for_profile(session: AsyncSession, profile: UserPreferenceProfile) -> int:
    """当用户画像（学历、政治面貌、专业大类、意向城市）变更时，重新推演全域招考岗位的四重硬门槛与契合度得分"""
    stmt = select(JobPosting).options(selectinload(JobPosting.advice))
    res = await session.execute(stmt)
    jobs = list(res.scalars().all())

    for job in jobs:
        if job.posting_type == "CIVIL_EXAM":
            eval_res = MatchingAgent.evaluate_civil_service(
                post_name=job.job_title,
                authority_name=job.org_name,
                degree_req=job.degree_req or "硕士",
                target_majors=job.major_reqs or [],
                political_req=job.political_req or "不限",
                is_fresh_only=job.is_fresh_only,
                profile=profile
            )
        else:
            eval_res = await MatchingAgent.evaluate_enterprise_job(
                job_title=job.job_title,
                company_name=job.org_name,
                work_locations=job.work_locations or [],
                degree_req=job.degree_req or "本科及以上",
                major_reqs=job.major_reqs or [],
                responsibilities=job.job_title,
                requirements=" ".join(job.major_reqs or []),
                profile=profile
            )

        if job.advice:
            job.advice.match_score = eval_res["match_score"]
            job.advice.match_level = eval_res["match_level"]
            job.advice.qualification_status = eval_res["qualification_status"]
            job.advice.highlights = eval_res["highlights"]
            job.advice.gaps = eval_res["gaps"]
            job.advice.action_advice = eval_res["action_advice"]
            job.advice.interview_tips = eval_res["interview_tips"]
        else:
            advice = JobMatchAdvice(
                job_id=job.id,
                posting_type=job.posting_type,
                match_score=eval_res["match_score"],
                match_level=eval_res["match_level"],
                qualification_status=eval_res["qualification_status"],
                highlights=eval_res["highlights"],
                gaps=eval_res["gaps"],
                action_advice=eval_res["action_advice"],
                interview_tips=eval_res["interview_tips"]
            )
            session.add(advice)

    await session.commit()
    return len(jobs)
