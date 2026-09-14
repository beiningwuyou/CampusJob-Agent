from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import JobPosting, JobMatchAdvice, ApplicationTrackRecord

SAMPLE_JOBS = [
    {
        "org_name": "华为技术有限公司",
        "job_title": "通用软件开发工程师 (2027届校招提前批)",
        "posting_type": "ENTERPRISE",
        "category": "综合类",
        "work_locations": ["杭州", "深圳"],
        "salary_desc": "20k-35k × 15薪",
        "degree_req": "硕士研究生及以上",
        "major_reqs": ["计算机科学与技术", "软件工程", "电子信息"],
        "is_fresh_only": True,
        "full_jd_json": {"summary": "负责华为云基础设施、分布式高可用架构及微服务组件的系统级软件研发与性能调优。"},
        "talk_location": "高校大学生活动中心剧场",
        "talk_time": datetime.now() + timedelta(hours=3),
        "apply_ddl": datetime.now() + timedelta(days=20),
        "apply_url": "https://career.huawei.com",
        "match_score": 94,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["薪资具有高度竞争力", "硕士学历与工科背景高度匹配", "直通研发核心平台团队"],
        "gaps": []
    },
    {
        "org_name": "中共浙江省委组织部 / 杭州市委办公厅",
        "job_title": "数字化改革与政务大数据专岗 (2027年定向选调)",
        "posting_type": "CIVIL_EXAM",
        "category": "综合类",
        "work_locations": ["杭州市"],
        "salary_desc": "机关事业编制 + 人才房补",
        "degree_req": "硕士研究生及以上",
        "major_reqs": ["计算机类", "信息与通信工程", "软件工程"],
        "political_req": "中共党员",
        "is_fresh_only": True,
        "full_jd_json": {"summary": "全省党政机关统一定向选调生，派驻市县数据资源管理局开展数字政务系统架构设计及应用推广。"},
        "talk_location": "高校学术报告厅 / 线下专场",
        "talk_time": datetime.now() + timedelta(days=2, hours=4),
        "apply_ddl": datetime.now() + timedelta(days=12),
        "apply_url": "http://gwy.zjks.gov.cn",
        "match_score": 96,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["党员身份完全契合", "应届硕士对口专业免去基层锻炼要求", "省市直属编制待遇"],
        "gaps": []
    },
    {
        "org_name": "美团",
        "job_title": "后端开发工程师 (北斗计划·技术极客提前批)",
        "posting_type": "ENTERPRISE",
        "category": "综合类",
        "work_locations": ["北京", "上海"],
        "salary_desc": "30k-45k × 15.5薪",
        "degree_req": "硕士研究生",
        "major_reqs": ["计算机", "软件", "应用数学"],
        "is_fresh_only": True,
        "full_jd_json": {"summary": "核心本地商业平台架构部，承载亿级高并发订单与交易履约引擎设计。"},
        "talk_location": "线上直播空中宣讲会",
        "talk_time": datetime.now() + timedelta(days=1, hours=6),
        "apply_ddl": datetime.now() + timedelta(hours=6),
        "apply_url": "https://zhaopin.meituan.com",
        "match_score": 88,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["超一线顶薪标准", "分布式实战经历高度吻合"],
        "gaps": ["仅剩6小时网申窗口，需立刻提交"]
    },
    {
        "org_name": "阿里巴巴集团 · 阿里云",
        "job_title": "分布式存储开发工程师 (研发提前批)",
        "posting_type": "ENTERPRISE",
        "category": "综合类",
        "work_locations": ["杭州", "北京"],
        "salary_desc": "25k-40k × 16薪",
        "degree_req": "硕士及以上",
        "major_reqs": ["计算机科学", "软件工程"],
        "is_fresh_only": True,
        "full_jd_json": {"summary": "参与盘古分布式文件系统、对象存储 OSS 底层核心研发与性能瓶颈攻关。"},
        "talk_location": "高校教学楼报告厅301",
        "talk_time": datetime.now() + timedelta(days=3),
        "apply_ddl": datetime.now() + timedelta(hours=14),
        "apply_url": "https://talent.alibaba.com",
        "match_score": 91,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["国内存储头部团队", "高可用架构课题直推通道"],
        "gaps": []
    },
    {
        "org_name": "招商银行总行金融科技联合体",
        "job_title": "金融科技研发工程师 (FinTech管培生)",
        "posting_type": "ENTERPRISE",
        "category": "综合类",
        "work_locations": ["深圳", "杭州"],
        "salary_desc": "22k-32k × 16薪",
        "degree_req": "硕士研究生及以上",
        "major_reqs": ["计算机", "软件工程", "金融科技"],
        "is_fresh_only": True,
        "full_jd_json": {"summary": "负责招商银行一网通、核心账务系统数字化转型与金融大模型私有化部署。"},
        "talk_location": "杭州JW万豪酒店三层大宴会厅",
        "talk_time": datetime.now() + timedelta(days=4),
        "apply_ddl": datetime.now() + timedelta(days=15),
        "apply_url": "https://career.cmbchina.com",
        "match_score": 86,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["总行正式编制", "六险二金福利全面", "长三角与大湾区双选"],
        "gaps": []
    },
    {
        "org_name": "国家电网大数据中心",
        "job_title": "电力大数据分析与云平台研发岗 (统考一批)",
        "posting_type": "ENTERPRISE",
        "category": "综合类",
        "work_locations": ["北京", "南京"],
        "salary_desc": "央企本部薪酬 + 解决北京户口指标",
        "degree_req": "硕士研究生及以上",
        "major_reqs": ["计算机类", "电气工程", "大数据技术"],
        "political_req": "中共党员优先",
        "is_fresh_only": True,
        "full_jd_json": {"summary": "承建全国电网智能调度与电力现货交易微服务集群。"},
        "talk_location": "清华大学二教报告厅",
        "talk_time": datetime.now() + timedelta(days=5),
        "apply_ddl": datetime.now() + timedelta(days=22),
        "apply_url": "https://zhaopin.sgcc.com.cn",
        "match_score": 89,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["特大型央企正式工", "进京指标通道明确"],
        "gaps": []
    },
    {
        "org_name": "国家税务总局浙江省税务局",
        "job_title": "信息系统运维与网络安全管理一级行政执法员",
        "posting_type": "CIVIL_EXAM",
        "category": "综合类",
        "work_locations": ["杭州市", "宁波市"],
        "salary_desc": "中央行政编制 (国考)",
        "degree_req": "本科及以上 (限硕士报考岗位)",
        "major_reqs": ["计算机科学与技术", "网络空间安全"],
        "is_fresh_only": True,
        "full_jd_json": {"summary": "金税四期工程核心数据库日常容灾维护、网络安全等级保护自查及日常税务执法。"},
        "talk_location": "国考统一报名通道",
        "talk_time": None,
        "apply_ddl": datetime.now() + timedelta(days=28),
        "apply_url": "http://bm.scs.gov.cn",
        "match_score": 84,
        "match_level": "MEDIUM",
        "qualification_status": "ELIGIBLE",
        "highlights": ["国家公务员行政编制", "专业科目完全对应计算机大类"],
        "gaps": ["竞争比预计超 1:80，需提早刷申论真题"]
    },
    {
        "org_name": "腾讯科技 (深圳) 有限公司",
        "job_title": "后台开发工程师 (PCG/TEG提前批)",
        "posting_type": "ENTERPRISE",
        "category": "综合类",
        "work_locations": ["深圳", "上海"],
        "salary_desc": "22k-36k × 16薪",
        "degree_req": "硕士及以上",
        "major_reqs": ["计算机类", "软件工程"],
        "is_fresh_only": True,
        "full_jd_json": {"summary": "海量高并发分布式后台服务开发，涉及微服务、高性能 RPC 框架与缓存设计。"},
        "talk_location": "浙江大学玉泉校区永谦活动中心",
        "talk_time": datetime.now() + timedelta(days=1),
        "apply_ddl": datetime.now() + timedelta(days=18),
        "apply_url": "https://join.qq.com",
        "match_score": 93,
        "match_level": "HIGH",
        "qualification_status": "ELIGIBLE",
        "highlights": ["业务基建核心团队", "面试流程进展迅速"],
        "gaps": []
    },
    {
        "org_name": "中共浙江省委统战部",
        "job_title": "侨务综合管理专岗 (2027年省考招录)",
        "posting_type": "CIVIL_EXAM",
        "category": "综合类",
        "work_locations": ["杭州市"],
        "salary_desc": "省直行政编制待遇",
        "degree_req": "硕士研究生及以上",
        "major_reqs": ["法学", "社会学类"],
        "political_req": "中共党员",
        "is_fresh_only": False,
        "full_jd_json": {"summary": "负责全省侨务政策综合研究、基层侨务统筹及涉侨权益保障工作。"},
        "talk_location": "浙江省公务员录用系统",
        "talk_time": None,
        "apply_ddl": datetime.now() + timedelta(days=16),
        "apply_url": "http://gwy.zjks.gov.cn",
        "match_score": 0,
        "match_level": "LOW",
        "qualification_status": "DISQUALIFIED",
        "highlights": [],
        "gaps": [
            "政治面貌硬门禁不匹配 (岗位限中共正式党员，当前画像为共青团员)",
            "专业学科代码不符 (岗位限 0301 法学，当前画像为 0812 计算机工学硕士)"
        ]
    }
]

async def init_preset_jobs_and_tracker(session: AsyncSession) -> int:
    """系统冷启动时，自动注入真实高质量校招与公考种子岗位，并联动生成追踪记录"""
    now = datetime.now()
    created_jobs = []

    for item in SAMPLE_JOBS:
        exists_stmt = select(JobPosting).where(
            JobPosting.org_name == item["org_name"],
            JobPosting.job_title == item["job_title"]
        )
        existing = (await session.execute(exists_stmt)).scalar_one_or_none()
        if existing:
            continue

        job = JobPosting(
            org_name=item["org_name"],
            job_title=item["job_title"],
            posting_type=item["posting_type"],
            category=item.get("category", "综合类"),
            work_locations=item["work_locations"],
            salary_desc=item["salary_desc"],
            degree_req=item["degree_req"],
            major_reqs=item["major_reqs"],
            political_req=item.get("political_req"),
            is_fresh_only=item.get("is_fresh_only", True),
            talk_location=item.get("talk_location"),
            talk_time=item.get("talk_time"),
            apply_ddl=item.get("apply_ddl"),
            apply_url=item.get("apply_url"),
            full_jd_json=item.get("full_jd_json", {})
        )
        session.add(job)
        await session.flush()

        advice = JobMatchAdvice(
            job_id=job.id,
            posting_type=job.posting_type,
            match_score=item["match_score"],
            match_level=item["match_level"],
            qualification_status=item["qualification_status"],
            highlights=item["highlights"],
            gaps=item["gaps"],
            action_advice="建议根据本岗位核心考查维度针对性微调【简历版本】，并在截止前 48h 完成投递。"
        )
        session.add(advice)
        created_jobs.append(job)

    # 如果有新创建的岗位且看板尚无记录，生成示范追踪
    track_count_res = await session.execute(select(func.count(ApplicationTrackRecord.id)))
    track_count = track_count_res.scalar() or 0
    if track_count == 0 and created_jobs:
        stage_presets = [
            ("APPLIED", "2027届秋招提前批", False, now + timedelta(days=2), "简历筛选与测评流转中"),
            ("WRITTEN_EXAM", "2027年定向选调", True, now + timedelta(hours=4), "招行金科统考机试 (ACM模式)"),
            ("INTERVIEW", "北斗计划极客专场", True, now + timedelta(days=1, hours=2), "美团基础研发业务二面 (双机位)"),
            ("REVIEW_CHECK", "秋招常规批", False, now + timedelta(days=5), "政审资格复审与档案核验"),
            ("OFFER_ACCEPTED", "提前批正式意向书", False, None, "已签订两方就业意向协议")
        ]

        for idx, (stage, batch, is_crit, node_time, node_desc) in enumerate(stage_presets):
            if idx < len(created_jobs):
                target_job = created_jobs[idx]
                rec = ApplicationTrackRecord(
                    job_id=target_job.id,
                    current_stage=stage,
                    batch_title=batch,
                    resume_version="v4.2_分布式重构.pdf",
                    is_critical=is_crit,
                    next_node_time=node_time,
                    next_node_desc=node_desc,
                    notes="系统智能流水线自动跟踪"
                )
                session.add(rec)

    await session.commit()
    return len(created_jobs)
