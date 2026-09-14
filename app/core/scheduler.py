from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.repositories.source_repo import SourceRepository
from app.db.repositories.job_repo import JobRepository
from app.services.scraper_service import ScraperService
from app.services.mail_service import MailService

scheduler = AsyncIOScheduler()

async def scheduled_feed_crawl_job():
    """定时抓取所有活跃信源任务"""
    async with AsyncSessionLocal() as session:
        source_repo = SourceRepository(session)
        sources = await source_repo.list_sources()
        for src in sources:
            if src.status != "ACTIVE":
                continue
            try:
                posts = await ScraperService.parse_rss_feed(src.feed_url)
                for p in posts:
                    await source_repo.save_raw_post(
                        source_id=src.id,
                        source_category=src.source_category,
                        source_url=p["url"],
                        title=p["title"],
                        extracted_text=p["clean_text"],
                        image_urls=p["image_urls"]
                    )
            except Exception:
                pass

async def scheduled_daily_briefing_job():
    """定时发送每日求职与招考早报邮件"""
    async with AsyncSessionLocal() as session:
        job_repo = JobRepository(session)

        # 拉取今日高分企业岗位
        ent_jobs, _ = await job_repo.list_jobs(posting_type="ENTERPRISE", min_score=75, limit=5)
        # 拉取符合资格的公考编制
        civ_jobs, _ = await job_repo.list_jobs(posting_type="CIVIL_EXAM", limit=5)

        recipient = settings.NOTIFICATION_RECIPIENT_EMAIL or settings.SMTP_USER
        if recipient:
            top_jobs_data = [{
                "org_name": j.org_name,
                "job_title": j.job_title,
                "score": j.advice.match_score if j.advice else 85,
                "work_locations": j.work_locations,
                "salary_desc": j.salary_desc,
                "apply_ddl": str(j.apply_ddl) if j.apply_ddl else None,
                "talk_time": j.talk_time,
                "talk_location": j.talk_location
            } for j in ent_jobs]

            civ_data = [{
                "org_name": c.org_name,
                "job_title": c.job_title,
                "post_code": c.post_code,
                "apply_start": str(c.apply_start) if c.apply_start else None,
                "apply_ddl": str(c.apply_ddl) if c.apply_ddl else None,
            } for c in civ_jobs]

            await MailService.send_daily_briefing(
                recipient_email=recipient,
                top_jobs=top_jobs_data,
                civil_exams=civ_data,
                upcoming_events=[]
            )

def start_scheduler():
    """启动全局定时调度器"""
    if not scheduler.running:
        # 定时全网抓取
        scheduler.add_job(
            scheduled_feed_crawl_job,
            "interval",
            hours=settings.AUTO_CRAWL_INTERVAL_HOURS,
            id="feed_crawl_job"
        )
        # 每日求职早报
        scheduler.add_job(
            scheduled_daily_briefing_job,
            "cron",
            hour=settings.DAILY_BRIEF_HOUR,
            minute=settings.DAILY_BRIEF_MINUTE,
            id="daily_briefing_job"
        )
        scheduler.start()

def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
