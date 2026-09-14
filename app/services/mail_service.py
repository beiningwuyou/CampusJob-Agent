import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List
import aiosmtplib
from icalendar import Calendar, Event, Alarm
from app.core.config import settings

class MailService:
    @classmethod
    def generate_ics_calendar(
        cls,
        events: List[dict]
    ) -> bytes:
        """根据日程列表生成符合 RFC 5545 标准的 .ics 日历文件"""
        cal = Calendar()
        cal.add("prodid", "-//CampusJob-Agent//CN")
        cal.add("version", "2.0")

        for ev in events:
            event = Event()
            event.add("summary", ev.get("title", "求职日程"))
            start_dt = ev.get("start_time")
            if isinstance(start_dt, datetime.datetime):
                event.add("dtstart", start_dt)
                event.add("dtend", ev.get("end_time") or (start_dt + datetime.timedelta(hours=2)))
            event.add("location", ev.get("location", ""))
            event.add("description", ev.get("description", ""))

            # 提前 30 分钟强提醒
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", "日程即将开始，请提前做好准备")
            alarm.add("trigger", datetime.timedelta(minutes=-30))
            event.add_component(alarm)

            cal.add_component(event)

        return cal.to_ical()

    @classmethod
    async def send_daily_briefing(
        cls,
        recipient_email: str,
        top_jobs: List[dict],
        civil_exams: List[dict],
        upcoming_events: List[dict]
    ) -> bool:
        """异步发送响应式 HTML 求职与招考早报及 ICS 附件"""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            # 未配置时返回假成功，不阻断主流程
            return False

        message = MIMEMultipart("mixed")
        today_str = datetime.date.today().strftime("%Y年%m月%d日")
        message["Subject"] = f"【CampusJob 早报】{today_str} 精选校招与招考速递"
        message["From"] = f"{settings.SMTP_SENDER_NAME} <{settings.SMTP_USER}>"
        message["To"] = recipient_email

        # 构造 HTML 邮件体
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
                .header {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); color: #ffffff; padding: 24px; }}
                .header h1 {{ margin: 0; font-size: 20px; }}
                .section {{ padding: 20px; border-bottom: 1px solid #f1f5f9; }}
                .section-title {{ font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 12px; border-left: 4px solid #2563eb; padding-left: 8px; }}
                .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 10px; }}
                .badge {{ display: inline-block; padding: 2px 8px; font-size: 12px; font-weight: bold; border-radius: 4px; }}
                .badge-green {{ background: #dcfce7; color: #15803d; }}
                .badge-blue {{ background: #dbeafe; color: #1d4ed8; }}
                .footer {{ text-align: center; color: #94a3b8; font-size: 12px; padding: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 CampusJob 智能求职与招考精选早报</h1>
                    <p style="margin: 6px 0 0 0; opacity: 0.85; font-size: 13px;">{today_str} | 本地隐私沙箱已保护您的敏感个人信息</p>
                </div>

                <div class="section">
                    <div class="section-title">💼 今日高契合企业校招岗位 (Top 推荐)</div>
        """

        for job in top_jobs[:4]:
            score = job.get("score", 85)
            html_content += f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 15px; color: #0f172a;">{job.get('org_name')} - {job.get('job_title')}</strong>
                            <span class="badge badge-green">契合度: {score}分</span>
                        </div>
                        <p style="margin: 6px 0; font-size: 13px; color: #475569;">地点: {', '.join(job.get('work_locations', []))} | 薪资: {job.get('salary_desc') or '面议'}</p>
                        <p style="margin: 0; font-size: 12px; color: #64748b;">网申截止: {job.get('apply_ddl') or '招满即止'}</p>
                    </div>
            """

        html_content += """
                </div>

                <div class="section">
                    <div class="section-title">🏛️ 符合资格的公考编制招考简讯</div>
        """

        for exam in civil_exams[:3]:
            html_content += f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 15px; color: #0f172a;">{exam.get('org_name')}</strong>
                            <span class="badge badge-blue">✅ 资格符合</span>
                        </div>
                        <p style="margin: 4px 0; font-size: 13px; color: #334155;">职位: {exam.get('job_title')} (代码: {exam.get('post_code') or '未注明'})</p>
                        <p style="margin: 0; font-size: 12px; color: #e11d48;">报名时间: {exam.get('apply_start') or '近日'} 至 {exam.get('apply_ddl') or '见公告'}</p>
                    </div>
            """

        html_content += """
                </div>

                <div class="section">
                    <div class="section-title">📅 今日/明日重要日程与宣讲会</div>
        """

        if not upcoming_events:
            html_content += "<p style='color: #94a3b8; font-size: 13px;'>近两日暂无待办宣讲或截止节点。</p>"
        else:
            for ev in upcoming_events:
                html_content += f"""
                    <div style="padding: 6px 0; border-bottom: 1px dashed #e2e8f0; font-size: 13px;">
                        ⏰ <strong>{ev.get('title')}</strong> - <span style="color: #64748b;">{ev.get('location') or '线上网申'}</span>
                    </div>
                """

        html_content += """
                </div>

                <div class="footer">
                    <p>由 CampusJob-Agent 本地智能系统自动化编排并生成</p>
                    <p>随信附带 .ics 日历文件，支持在 iPhone/Mac/Windows 日历中一键导入</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 挂载 HTML
        msg_alternative = MIMEMultipart("alternative")
        msg_alternative.attach(MIMEText(html_content, "html", "utf-8"))
        message.attach(msg_alternative)

        # 挂载 ICS 附件
        if upcoming_events or top_jobs:
            all_cal_events = upcoming_events.copy()
            for j in top_jobs:
                if j.get("talk_time"):
                    all_cal_events.append({
                        "title": f"【宣讲会】{j.get('org_name')}",
                        "start_time": j.get("talk_time"),
                        "location": j.get("talk_location"),
                        "description": f"岗位: {j.get('job_title')}"
                    })
            ics_bytes = cls.generate_ics_calendar(all_cal_events)
            part = MIMEBase("text", "calendar", method="REQUEST", name="campus_job_schedule.ics")
            part.set_payload(ics_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename=campus_job_schedule.ics")
            message.attach(part)

        # 异步 SMTP 发送
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_SSL,
                timeout=15.0
            )
            return True
        except Exception:
            return False
