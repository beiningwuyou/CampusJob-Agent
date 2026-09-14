from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.tracker_repo import TrackerRepository
from app.db.repositories.job_repo import JobRepository
from app.schemas.tracker import (
    TrackerKanbanResponse, TrackerItemResponse, TrackerMoveStageRequest, TrackerCreateRequest,
    TrackerIngestRequest, TrackerIngestResponse, ExtractedEvent, TrackerIngestConfirmRequest,
    TrackerBatchImportRequest
)

router = APIRouter(prefix="/tracker", tags=["投递追踪看板"])

def _to_tracker_item_resp(r) -> TrackerItemResponse:
    job = r.job
    return TrackerItemResponse(
        id=r.id,
        job_id=r.job_id,
        org_name=job.org_name if job else "未知机构",
        job_title=job.job_title if job else "未知岗位",
        posting_type=job.posting_type if job else "ENTERPRISE",
        salary_desc=job.salary_desc if job else None,
        work_locations=job.work_locations if job else [],
        current_stage=r.current_stage,
        batch_title=r.batch_title,
        resume_version=r.resume_version,
        next_node_time=r.next_node_time,
        next_node_desc=r.next_node_desc,
        is_critical=r.is_critical,
        notes=r.notes,
        match_score=job.advice.match_score if job and job.advice else 85,
        apply_url=job.apply_url if job else None,
        updated_at=r.updated_at
    )

@router.get("", response_model=TrackerKanbanResponse)
async def get_tracker_kanban(db: AsyncSession = Depends(get_db)):
    """获取五大阶段看板各列数据与核心统计指标"""
    repo = TrackerRepository(db)
    stages = await repo.list_by_stages()
    metrics = await repo.get_metrics()

    # 若暂无记录，则自动从现有 job_posting 生成初始演示追踪记录
    total_records = sum(len(v) for v in stages.values())
    if total_records == 0:
        job_repo = JobRepository(db)
        jobs, _ = await job_repo.list_jobs(limit=10)
        demo_stages = ["APPLIED", "WRITTEN_EXAM", "INTERVIEW", "REVIEW_CHECK", "OFFER_ACCEPTED"]
        now = datetime.now()
        for idx, job in enumerate(jobs):
            stage = demo_stages[idx % len(demo_stages)]
            rec = await repo.add_or_get_by_job_id(
                job_id=job.id,
                stage=stage,
                batch_title="2027届校园招聘提前批" if job.posting_type == "ENTERPRISE" else "2027年公考招录",
                resume_version="v4.2_分布式重构.pdf"
            )
            rec.is_critical = (idx == 1 or idx == 3)
            if idx == 1:
                rec.next_node_time = now + timedelta(hours=4)
                rec.next_node_desc = "招行金科统考机试 (ACM模式)"
            elif idx == 2:
                rec.next_node_time = now + timedelta(days=1, hours=2)
                rec.next_node_desc = "淘天分布式技术二面 (视频)"
            await db.commit()
        # 重新拉取
        stages = await repo.list_by_stages()
        metrics = await repo.get_metrics()

    formatted_stages = {}
    for stage_key, records in stages.items():
        formatted_stages[stage_key] = [_to_tracker_item_resp(r) for r in records]

    return TrackerKanbanResponse(
        metrics=metrics,
        stages=formatted_stages
    )

@router.get("/export")
async def export_tracker_csv(db: AsyncSession = Depends(get_db)):
    """导出全量投递全景追踪记录为 CSV 档案"""
    import csv
    import io
    from fastapi.responses import Response

    repo = TrackerRepository(db)
    stages = await repo.list_by_stages()
    records = []
    for r_list in stages.values():
        records.extend(r_list)

    stage_names = {
        "APPLIED": "已投递/待初筛",
        "WRITTEN_EXAM": "笔试/测评进行中",
        "INTERVIEW": "业务技术面试",
        "REVIEW_CHECK": "背调/资格复审",
        "OFFER_ACCEPTED": "已录用/已接Offer"
    }

    output = io.StringIO()
    # 写入 UTF-8 BOM，确保 Excel 打开中文不乱码
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "记录编号", "单位/企业名称", "投递岗位", "招考/校招大类", "当前阶段",
        "投递批次", "使用简历版本", "下一节点时间", "待办事项描述",
        "是否紧急", "契合度得分", "更新时间", "备注"
    ])

    for r in records:
        job = r.job
        writer.writerow([
            r.id,
            job.org_name if job else "未知单位",
            job.job_title if job else "未知岗位",
            "体制内公考" if job and job.posting_type == "CIVIL_EXAM" else "企业校招",
            stage_names.get(r.current_stage, r.current_stage),
            r.batch_title or "",
            r.resume_version or "",
            r.next_node_time.strftime("%Y-%m-%d %H:%M") if r.next_node_time else "暂无排期",
            r.next_node_desc or "暂无",
            "紧急" if r.is_critical else "常规",
            job.advice.match_score if job and job.advice else 85,
            r.updated_at.strftime("%Y-%m-%d %H:%M") if r.updated_at else "",
            r.notes or ""
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=CampusJob_Tracker_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@router.patch("/{record_id}/move", response_model=TrackerItemResponse)
async def move_tracker_stage(
    record_id: int,
    req: TrackerMoveStageRequest,
    db: AsyncSession = Depends(get_db)
):
    """拖拽或手动流转投递阶段"""
    repo = TrackerRepository(db)
    record = await repo.move_stage(
        record_id=record_id,
        new_stage=req.new_stage,
        note=req.note,
        next_node_time=req.next_node_time,
        next_node_desc=req.next_node_desc
    )
    if not record:
        raise HTTPException(status_code=404, detail="跟踪记录不存在")
    return _to_tracker_item_resp(record)

@router.post("", response_model=TrackerItemResponse)
async def create_tracker_record(
    req: TrackerCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """手动或从岗位详情推入投递追踪"""
    repo = TrackerRepository(db)
    record = await repo.add_or_get_by_job_id(
        job_id=req.job_id,
        stage=req.stage,
        batch_title=req.batch_title or "秋招常规批次",
        resume_version=req.resume_version or "默认脱敏简历.pdf"
    )
    return _to_tracker_item_resp(record)


@router.post("/ingest", response_model=TrackerIngestResponse)
async def ingest_notification_signal(
    req: TrackerIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """智能嗅探并结构化提取面试邀请、笔试短信或 Offer 邮件中的关键招聘事件"""
    import re
    from datetime import datetime, timedelta

    text = req.raw_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="通知文本不能为空")

    now = datetime.now()

    # 1. 抽取机构名
    candidate_org = "未知机构"
    # 优先提取【】中的企业名
    bracket_match = re.search(r'【([^】]+)】', text)
    if bracket_match:
        b_content = bracket_match.group(1).strip()
        for sep in ["招聘", "HR", "校招", "笔试", "面试", "通知"]:
            if sep in b_content:
                b_content = b_content.split(sep)[0].strip()
        if b_content:
            candidate_org = b_content

    if candidate_org == "未知机构":
        known_orgs = ["腾讯", "阿里巴巴", "阿里", "字节跳动", "字节", "美团", "华为", "招商银行", "工商银行", "网易", "快手", "百度", "浙江省考", "国家电网", "拼多多", "微软"]
        for o in known_orgs:
            if o in text:
                candidate_org = "腾讯科技" if o == "腾讯" else ("阿里巴巴" if o in ["阿里", "阿里巴巴"] else ("字节跳动" if o in ["字节", "字节跳动"] else o))
                break

    # 2. 识别事件类型与阶段映射
    mapped_stage = "APPLIED"
    event_type = "网申状态更新"

    if any(kw in text for kw in ["录用", "正式意向", "意向书", "Offer", "offer", "拟录取", "拟录用"]):
        mapped_stage = "OFFER_ACCEPTED"
        event_type = "意向录用 / Offer"
    elif any(kw in text for kw in ["政审", "背调", "体检", "终面", "HR面", "资格复审", "组织考察"]):
        mapped_stage = "REVIEW_CHECK"
        event_type = "HR终审 / 考察"
    elif any(kw in text for kw in ["二面", "一面", "三面", "技术面", "业务面", "初面", "复试", "面试邀请", "视频面试"]):
        mapped_stage = "INTERVIEW"
        event_type = "业务 / 技术面试"
    elif any(kw in text for kw in ["笔试", "机考", "测评", "牛客", "行测", "统考", "机试"]):
        mapped_stage = "WRITTEN_EXAM"
        event_type = "统一笔试 / 机考"
    elif any(kw in text for kw in ["网申", "初审", "简历筛选", "简历通过"]):
        mapped_stage = "APPLIED"
        event_type = "网申初审"

    # 3. 抽取时间与倒计时推算
    scheduled_time = None
    scheduled_time_desc = None

    # 匹配 "明天 14:00" / "明日 14:30" / "9月15日 19:00" 等
    if "明天" in text or "明日" in text:
        time_match = re.search(r'(\d{1,2})[:：](\d{2})', text)
        hour = int(time_match.group(1)) if time_match else 14
        minute = int(time_match.group(2)) if time_match else 0
        scheduled_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        scheduled_time_desc = f"明天 {hour:02d}:{minute:02d}"
    elif "后天" in text:
        time_match = re.search(r'(\d{1,2})[:：](\d{2})', text)
        hour = int(time_match.group(1)) if time_match else 14
        minute = int(time_match.group(2)) if time_match else 0
        scheduled_time = (now + timedelta(days=2)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        scheduled_time_desc = f"后天 {hour:02d}:{minute:02d}"
    else:
        date_match = re.search(r'(\d{1,2})月(\d{1,2})[日号]?\s*(\d{1,2})[:：](\d{2})', text)
        if date_match:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            hour = int(date_match.group(3))
            minute = int(date_match.group(4))
            scheduled_time = now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
            scheduled_time_desc = f"{month:02d}月{day:02d}日 {hour:02d}:{minute:02d}"

    if not scheduled_time_desc and scheduled_time:
        scheduled_time_desc = scheduled_time.strftime("%m月%d日 %H:%M")

    # 4. 抽取会议号 / 口令 / 链接
    meeting_match = re.search(r'(腾讯会议|Zoom|飞书会议|牛客|会议号|口令)[：:\s]*([A-Za-z0-9\-_]{4,20})', text)
    access_code = meeting_match.group(2) if meeting_match else None

    url_match = re.search(r'(https?://[^\s]+)', text)
    location_or_link = url_match.group(1) if url_match else ("腾讯会议 (线上)" if "腾讯会议" in text else ("牛客双机位" if "牛客" in text else "线上进行"))

    # 5. 查找现有 Tracker 中是否已存在对应机构记录
    repo = TrackerRepository(db)
    stages = await repo.list_by_stages()
    matched_tracker_id = None
    matched_job_title = None

    for r_list in stages.values():
        for r in r_list:
            if r.job and (candidate_org in r.job.org_name or r.job.org_name in candidate_org):
                matched_tracker_id = r.id
                matched_job_title = r.job.job_title
                break
        if matched_tracker_id:
            break

    summary = f"检测到【{candidate_org}】的【{event_type}】，安排于 {scheduled_time_desc or '近期通知'}。"

    from app.schemas.tracker import TrackerIngestResponse
    event_obj = ExtractedEvent(
        org_name=candidate_org,
        job_title=matched_job_title or "相关研发/管培岗位",
        event_type=event_type,
        mapped_stage=mapped_stage,
        scheduled_time_desc=scheduled_time_desc or "见通知正文",
        scheduled_time=scheduled_time,
        location_or_link=location_or_link,
        access_code=access_code,
        summary=summary,
        matched_tracker_id=matched_tracker_id
    )

    return TrackerIngestResponse(
        success=True,
        event=event_obj,
        matched_existing_record=bool(matched_tracker_id),
        confidence_score=95 if matched_tracker_id else 85
    )


@router.post("/ingest/confirm")
async def confirm_ingest_signal(
    req: TrackerIngestConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    """确认应用智能嗅探结果：一键持久化推进 Tracker 阶段，并在日历中自动装配同步日程"""
    repo = TrackerRepository(db)
    tracker_record = None

    if req.tracker_id:
        tracker_record = await repo.get_by_id(req.tracker_id)

    if not tracker_record:
        # 尝试通过机构名称模糊匹配
        stages = await repo.list_by_stages()
        for r_list in stages.values():
            for r in r_list:
                if r.job and (req.org_name in r.job.org_name or r.job.org_name in req.org_name):
                    tracker_record = r
                    break
            if tracker_record:
                break

    if tracker_record:
        # 更新现有记录
        await repo.move_stage(
            record_id=tracker_record.id,
            new_stage=req.target_stage,
            note=req.notes or f"通过智能通知嗅探自动推进至【{req.target_stage}】",
            next_node_time=req.node_time,
            next_node_desc=req.node_desc
        )
        final_id = tracker_record.id
    else:
        # 新增一条独立岗位并放入 Tracker
        job_repo = JobRepository(db)
        new_job = await job_repo.save_job_with_advice(
            job_data={
                "posting_type": "ENTERPRISE",
                "org_name": req.org_name,
                "job_title": req.job_title or "校招技术岗位",
                "category": "研发类",
                "work_locations": ["杭州", "上海"],
                "degree_req": "硕士",
                "major_reqs": ["计算机", "软件工程"],
                "apply_ddl": req.node_time
            },
            advice_data={
                "match_score": 90,
                "match_level": "HIGH",
                "qualification_status": "ELIGIBLE",
                "highlights": ["通过智能嗅探捕获投递信号"],
                "gaps": []
            }
        )
        new_tracker = await repo.add_or_get_by_job_id(
            job_id=new_job.id,
            stage=req.target_stage,
            batch_title="智能通知导入批次",
            resume_version="v4.2_分布式重构.pdf"
        )
        if req.node_time:
            new_tracker.next_node_time = req.node_time
            new_tracker.next_node_desc = req.node_desc or "重要求职节点"
            await db.commit()
        final_id = new_tracker.id

    return {
        "status": "success",
        "message": f"✅ 已成功将【{req.org_name}】推进至目标阶段并同步更新看板与日历！",
        "tracker_id": final_id,
        "target_stage": req.target_stage
    }

@router.post("/batch-import")
async def batch_import_tracker(
    req: TrackerBatchImportRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量从用户已有 Excel/表格/清单中导入求职投递记录"""
    repo = TrackerRepository(db)
    job_repo = JobRepository(db)
    imported_count = 0

    for item in req.items:
        new_job = await job_repo.save_job_with_advice(
            job_data={
                "posting_type": "CIVIL_SERVICE" if any(w in item.org_name for w in ["考公", "省考", "选调", "编制", "发改委", "税务"]) else "ENTERPRISE",
                "org_name": item.org_name.strip(),
                "job_title": item.job_title.strip() or "技术研发",
                "category": "综合类",
                "salary_desc": item.salary_desc or "面议",
                "work_locations": [item.location.strip()] if item.location else ["杭州"]
            },
            advice_data={
                "match_score": 88,
                "match_level": "HIGH",
                "qualification_status": "ELIGIBLE",
                "highlights": ["从用户已有求职清单/Excel批量导入"],
                "gaps": []
            }
        )
        rec = await repo.add_or_get_by_job_id(
            job_id=new_job.id,
            stage=item.stage,
            batch_title="存量求职资产迁移批次",
            resume_version="默认脱敏简历.pdf"
        )
        if item.notes:
            rec.notes = item.notes
            await db.commit()
        imported_count += 1

    return {
        "status": "success",
        "imported_count": imported_count,
        "message": f"成功批量迁移并导入 {imported_count} 项存量投递事项！"
    }

@router.post("/seed-presets")
async def seed_tracker_presets(
    db: AsyncSession = Depends(get_db)
):
    """一键装填经典双轨示范数据 (降低新用户上手阻力)"""
    from app.services.seed_data import init_preset_jobs_and_tracker
    await init_preset_jobs_and_tracker(db)
    return {
        "status": "success",
        "message": "已成功注入经典双轨求职示范数据（含阿里、美团、浙江选调、国家电网等）"
    }

