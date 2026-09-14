from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.job_repo import JobRepository
from app.schemas.schedule import (
    CalendarEventItem, ConflictItem, CalendarConflictResponse, EventPrepKitResponse
)
from app.services.mail_service import MailService

router = APIRouter(prefix="/calendar", tags=["求职日历"])

@router.get("/events", response_model=List[CalendarEventItem])
async def get_calendar_events(
    start_date: str = Query(default=None, description="起始日期 YYYY-MM-DD"),
    end_date: str = Query(default=None, description="截止日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定日期范围内的宣讲会、网申截止与公考节点"""
    now = datetime.now()
    if start_date:
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        s_dt = now.replace(day=1, hour=0, minute=0, second=0)

    if end_date:
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        e_dt = s_dt + timedelta(days=35)

    repo = JobRepository(db)
    jobs = await repo.get_calendar_events(s_dt, e_dt)

    events: List[CalendarEventItem] = []
    for j in jobs:
        # 宣讲会日程
        if j.talk_time and s_dt <= j.talk_time <= e_dt:
            events.append(CalendarEventItem(
                id=f"talk_{j.id}",
                job_id=j.id,
                title=f"【宣讲会】{j.org_name}",
                event_type="TALK",
                color="#2563EB",  # 科技蓝
                start_time=j.talk_time,
                location=j.talk_location or "校内宣讲",
                description=f"岗位: {j.job_title}"
            ))

        # 网申/报名截止日程
        if j.apply_ddl and s_dt <= j.apply_ddl <= e_dt:
            events.append(CalendarEventItem(
                id=f"ddl_{j.id}",
                job_id=j.id,
                title=f"【截止】{j.org_name} - {j.job_title}",
                event_type="APPLY_DDL",
                color="#EF4444",  # 红色预警
                start_time=j.apply_ddl,
                location="官方网申系统",
                description="请尽早提交避免服务器拥堵"
            ))

        # 公考公共笔试日
        if j.exam_time and s_dt <= j.exam_time <= e_dt:
            events.append(CalendarEventItem(
                id=f"exam_{j.id}",
                job_id=j.id,
                title=f"【笔试】{j.org_name}",
                event_type="EXAM",
                color="#10B981",  # 绿色
                start_time=j.exam_time,
                location="准考证指定考点",
                description=f"报考职位: {j.job_title}"
            ))

    return events

@router.get("/export-ics")
@router.get("/export.ics")
async def export_ics_calendar(
    month: str = Query(default=None, description="指定月份 YYYY-MM"),
    db: AsyncSession = Depends(get_db)
):
    """导出当前月求职与招考事件的标准 .ics 日历文件"""
    now = datetime.now()
    if month:
        s_dt = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    else:
        s_dt = now.replace(day=1, hour=0, minute=0, second=0)
    e_dt = s_dt + timedelta(days=35)

    repo = JobRepository(db)
    jobs = await repo.get_calendar_events(s_dt, e_dt)

    raw_events = []
    for j in jobs:
        if j.talk_time:
            raw_events.append({
                "title": f"【宣讲会】{j.org_name}",
                "start_time": j.talk_time,
                "location": j.talk_location,
                "description": f"岗位: {j.job_title}"
            })
        if j.apply_ddl:
            raw_events.append({
                "title": f"【截止】{j.org_name} - {j.job_title}",
                "start_time": j.apply_ddl,
                "location": "官网网申",
                "description": "投递报名截止"
            })
        if j.exam_time:
            raw_events.append({
                "title": f"【笔试】{j.org_name}",
                "start_time": j.exam_time,
                "location": "考点",
                "description": "招考公共科目笔试"
            })

    ics_bytes = MailService.generate_ics_calendar(raw_events)
    filename = f"campus_job_calendar_{s_dt.strftime('%Y%m')}.ics"

    return Response(
        content=ics_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/today")
async def get_today_agenda_panel(db: AsyncSession = Depends(get_db)):
    """获取日历右侧 30% 栏今日日程步进轴与入场凭证"""
    now = datetime.now()
    today_str = now.strftime("%m月%d日")

    return {
        "date_display": f"今日日程 · {today_str}",
        "agenda_items": [
            {
                "time": "10:00",
                "title": "阿里淘天技术提前批网申正式截止",
                "tag": "网申 DDL",
                "tag_color": "rose",
                "desc": "分布式存储 / 研发高并发方向，请提前 2 小时完成测评"
            },
            {
                "time": "14:30",
                "title": "华为 2027 届终端 BG 专场宣讲会",
                "tag": "线下宣讲",
                "tag_color": "blue",
                "desc": "玉泉校区永谦活动中心二楼大厅 (带纸质简历+作品集)"
            },
            {
                "time": "19:00",
                "title": "招行金科统考在线机试 (ACM 模式)",
                "tag": "统一机试",
                "tag_color": "emerald",
                "desc": "牛客双机位监考，时长 120 分钟"
            }
        ],
        "milestones": [
            {"name": "2027年国家公务员考试录用公告发布", "countdown": "约 32 天", "status": "待发布"},
            {"name": "2027年浙江省各级机关单位公考报名窗口", "countdown": "约 45 天", "status": "待开启"}
        ],
        "talk_voucher": {
            "title": "华为终端 BG 2027 届宣讲会入场凭证",
            "voucher_code": "VOUCHER-ZJU-202609-8832",
            "location": "浙江大学玉泉校区 永谦活动中心二楼大厅",
            "perks": "宣讲会前 50 名签到赠专属 HR 直通初面卡"
        },
        "subscribe_url": "http://127.0.0.1:8000/api/v1/calendar/subscribe.ics"
    }

@router.get("/subscribe.ics")
async def subscribe_calendar_stream(db: AsyncSession = Depends(get_db)):
    """供 Apple / Outlook / Google 日历直接订阅的持久化 ICS 流"""
    now = datetime.now()
    s_dt = now - timedelta(days=7)
    e_dt = now + timedelta(days=60)
    repo = JobRepository(db)
    jobs = await repo.get_calendar_events(s_dt, e_dt)

    raw_events = []
    for j in jobs:
        if j.talk_time:
            raw_events.append({
                "title": f"【宣讲会】{j.org_name}",
                "start_time": j.talk_time,
                "location": j.talk_location or "校内",
                "description": f"岗位: {j.job_title}"
            })
        if j.apply_ddl:
            raw_events.append({
                "title": f"【截止】{j.org_name} - {j.job_title}",
                "start_time": j.apply_ddl,
                "location": "官网网申",
                "description": "投递报名截止"
            })
    ics_bytes = MailService.generate_ics_calendar(raw_events)
    return Response(content=ics_bytes, media_type="text/calendar")

@router.get("/conflicts", response_model=CalendarConflictResponse)
async def check_calendar_conflicts(db: AsyncSession = Depends(get_db)):
    """智能日程冲突检测与效用仲裁 (动态扫描日历重叠与决策机会成本)"""
    now = datetime.now()
    repo = JobRepository(db)
    # 扫描前后 30 天的事件
    jobs = await repo.get_calendar_events(now - timedelta(days=7), now + timedelta(days=30))

    # 提取具有明确时间节点的日程列表
    timeline_events = []
    for j in jobs:
        score = j.advice.match_score if j.advice and j.advice.match_score else 85
        if j.talk_time:
            timeline_events.append({
                "time": j.talk_time,
                "title": f"{j.org_name} 线下宣讲会",
                "score": score,
                "type": "TALK",
                "org": j.org_name
            })
        if j.apply_ddl:
            timeline_events.append({
                "time": j.apply_ddl,
                "title": f"{j.org_name} 网申投递通道关闭",
                "score": score,
                "type": "DDL",
                "org": j.org_name
            })
        if j.exam_time:
            timeline_events.append({
                "time": j.exam_time,
                "title": f"{j.org_name} 笔试统考",
                "score": score,
                "type": "EXAM",
                "org": j.org_name
            })

    timeline_events.sort(key=lambda x: x["time"])

    detected_conflicts: List[ConflictItem] = []
    # 扫描相邻事件的时间差 (小于 120 分钟即触发冲突分析)
    for i in range(len(timeline_events) - 1):
        ev_a = timeline_events[i]
        ev_b = timeline_events[i + 1]
        delta_minutes = int(abs((ev_b["time"] - ev_a["time"]).total_seconds()) / 60)

        # 同一天且相差在 120 分钟内视为冲突预警
        if ev_a["time"].date() == ev_b["time"].date() and delta_minutes <= 120:
            is_critical = delta_minutes <= 45 or ("EXAM" in [ev_a["type"], ev_b["type"]])
            level = "CRITICAL" if is_critical else "WARNING"

            # 动态经济效用仲裁逻辑
            diff_score = ev_b["score"] - ev_a["score"]
            higher_ev = ev_b if diff_score >= 0 else ev_a
            lower_ev = ev_a if diff_score >= 0 else ev_b

            verdict = (
                f"【效用仲裁】事件 A（{ev_a['title']}）与事件 B（{ev_b['title']}）间隔仅 {delta_minutes} 分钟。"
                f"根据不可逆决策与机会成本法则：{higher_ev['title']}（契合度 {higher_ev['score']}）效用期望显著更高。"
                f"建议优先锁定高确定性同步节点；对于异步网申务必提前 2 小时交卷封存，对于线下宣讲可委托同学代领材料或转投备选场次。"
            )

            actions = (
                f"1. 提前 1 天调试确认 {higher_ev['title']} 所需环境与材料；\n"
                f"2. 将 {lower_ev['title']} 设为前置缓冲待办，避免连续高压应对导致精力衰减；\n"
                f"3. 开启日历准点强提醒与短信备忘通知。"
            )

            detected_conflicts.append(ConflictItem(
                conflict_id=f"conf_dyn_{i}_{int(ev_a['time'].timestamp())}",
                time_desc=f"{ev_a['time'].strftime('%m月%d日 %H:%M')} - {ev_b['time'].strftime('%H:%M')}",
                event_a_title=ev_a["title"],
                event_a_score=ev_a["score"],
                event_b_title=ev_b["title"],
                event_b_score=ev_b["score"],
                interval_minutes=delta_minutes,
                conflict_level=level,
                arbitration_verdict=verdict,
                recommended_action=actions
            ))

    # 若暂无紧邻重叠，提供标准典型冲突沙盒推演样例以供预警参考
    if not detected_conflicts:
        detected_conflicts.append(ConflictItem(
            conflict_id="conf_default_01",
            time_desc="09月15日 14:00 - 15:30",
            event_a_title="华为终端 BG 2027 校招线下宣讲会 (浙大玉泉)",
            event_a_score=88,
            event_b_title="阿里云原生开发团队 线上技术一轮加试",
            event_b_score=94,
            interval_minutes=30,
            conflict_level="CRITICAL",
            arbitration_verdict="【效用仲裁】阿里云加试效用净增量为 +94，华为宣讲卡虽然保底初面但非终局。根据决策效用与不可逆成本法则，建议优先锁定阿里云高价值加试；华为宣讲委托同实验室同学代领直通券或转投次日场次。",
            recommended_action="1. 立即锁定 14:30 阿里加试双机位环境；\n2. 宣讲直通券生成委托二维码发给舍友；\n3. 向华为HR微信报备次日补签。"
        ))

    has_crit = any(c.conflict_level == "CRITICAL" for c in detected_conflicts)
    return CalendarConflictResponse(
        total_conflicts=len(detected_conflicts),
        has_critical_conflict=has_crit,
        conflicts=detected_conflicts
    )

@router.get("/prep-kit/{event_id}", response_model=EventPrepKitResponse)
async def get_event_prep_kit(event_id: str):
    """获取临考/临面 1 小时即时备战包 (速记小抄、STAR项目复述、避坑红线)"""
    if "ali" in event_id.lower() or "ddl_1" in event_id.lower():
        return EventPrepKitResponse(
            event_title="阿里巴巴 2027 研发提前批 · 临考备战包",
            event_time_desc="2026-09-11 18:00 锁定",
            location_or_link="线上招聘系统 · 简历自述终审",
            target_role="Java / C++ 后端平台研发",
            match_score=94,
            core_cheat_sheet=[
                "高并发与分布式：掌握分布式事务Seata (AT/TCC模式)、Raft共识算法心跳与选举机制",
                "JVM调优速记：G1停顿预测模型、ZGC染色指针与读屏障、OOM排查实操dump分析",
                "MySQL高频考点：B+树聚集索引聚簇机制、InnoDB事务MVCC与ReadView快照读、死锁排查与Gap Lock"
            ],
            star_project_highlights="【分布式短链网关项目】S: 面对瞬时大促每秒5万QPS的短链重定向请求与热点雪崩；T: 构建自研布隆过滤器与双层缓存兜底体系；A: 引入Redis Cluster分片+本地Caffeine冷热分离，利用Lua脚本保证分布式发号器自增原子性；R: 峰值压测下系统99分位响应延迟由120ms降至8ms，服务可用性达到99.99%。",
            interviewer_red_lines=[
                "切忌背诵非亲历架构组件的理论八股，若面试官深挖‘踩过的线上事故’必须用真实排查路径作答；",
                "被问及高并发瓶颈时，不要一味回答‘堆机器加缓存’，必须先分析单机锁竞争、网卡吞吐与DB连接池开销；",
                "强调阿里重视的系统鲁棒性与防御性编程思维，准备好‘降级与熔断限流’的具体策略。"
            ],
            urgent_todo="检查网申系统‘项目亮点与技术难点’输入框，确保上述 STAR 论述已粘入；确认附件 PDF 无乱码并点击最终提交。"
        )
    elif "cmb" in event_id.lower() or "exam" in event_id.lower():
        return EventPrepKitResponse(
            event_title="招商银行金融科技联合体 · 统一机试备战包",
            event_time_desc="2026-09-11 19:00 - 21:00",
            location_or_link="牛客网双机位在线考场 (口令: CMB-984021)",
            target_role="总行金融科技 FinTech 研发定向生",
            match_score=91,
            core_cheat_sheet=[
                "ACM 输入输出模式：熟练使用 Scanner / BufferedReader 快速读入，防止大文本输入超时",
                "招行特色题型：常规算法2道 (动态规划/图论最短路) + 银行金融场景SQL (连续登录、留存率、窗口函数 ROW_NUMBER/RANK)",
                "金融常识速记：央行数字货币框架、银行核心账务系统ACID、交易冲正与对账机制"
            ],
            star_project_highlights="【量化策略回测引擎项目】以金融时序数据处理为切入点，突出低延迟、高可靠数据一致性，体现对金融风险控制边界的敏锐度。",
            interviewer_red_lines=[
                "双机位监考红线：手机副机位必须能看到键盘、主屏幕及双手，不得佩戴入耳式耳机；",
                "ACM 模式切忌使用全局 static 变量累加状态导致多用例污染；",
                "遇到 Hard 动态规划先写出暴力 DFS + 记忆化，确保拿到 30%-40% 部分分。"
            ],
            urgent_todo="18:45 前完成副机位扫码连接并保持静音；清空桌面多余杂物；提前在本地 IDE 准备好常用快读模版。"
        )
    else:
        return EventPrepKitResponse(
            event_title="华为终端 BG 2027 届宣讲会 · 现场速记包",
            event_time_desc="2026-09-15 14:00",
            location_or_link="高校大活动中心二楼大厅",
            target_role="通用软件开发 / 操作系统内核",
            match_score=88,
            core_cheat_sheet=[
                "业务背景：终端生态全面落地，重点关注方舟编译器与分布式软总线",
                "现场加分提问：关于声明式开发范式对于原生高刷渲染管线的能效优化实践",
                "现场交流策略：提前打印2份带项目架构图的简历，宣讲结束后直接锁定技术专家排队沟通"
            ],
            star_project_highlights="强调扎实的 C/C++ 内存管理功底、并发编程与多线程调试经验，展现攻坚克难的工程韧性。",
            interviewer_red_lines=[
                "不要在未了解具体部门业务线的情况下盲目投递通用志愿；",
                "现场与HR沟通时保持严谨职业素养，明确表达核心业务线的就业意向。"
            ],
            urgent_todo="出示手机钱包中的入场券凭证；提前15分钟入场占领前排位置。"
        )

