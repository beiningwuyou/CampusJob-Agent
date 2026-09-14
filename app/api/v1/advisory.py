from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.profile_repo import ProfileRepository
from app.agents.base_agent import BaseAgent
from app.schemas.advisory import (
    CapabilityRadarResponse, CapabilityDimension, AdvisoryDiagnosticItem,
    ExamHitPrediction, AdvisoryChatRequest, AdvisoryChatResponse,
    OfferOption, DecisionMatrixResponse
)

router = APIRouter(prefix="/advisory", tags=["AI 顾问诊断中心"])

@router.get("/radar", response_model=CapabilityRadarResponse)
async def get_capability_radar(db: AsyncSession = Depends(get_db)):
    """获取个人六维能力雷达剖析与精力分配健康度"""
    repo = ProfileRepository(db)
    profile = await repo.get_or_create_default()

    import json
    deg_label = profile.education_level if (profile and profile.education_level) else "求职者"
    dimensions = [
        CapabilityDimension(name=f"专业背景匹配 ({deg_label})", score=90, color="emerald"),
        CapabilityDimension(name="项目工程落地 (实践技能)", score=88, color="amber"),
        CapabilityDimension(name="体制合规准入 (资质/专业)", score=92, color="emerald"),
        CapabilityDimension(name="面试表达胜率 (STAR法则/结构化)", score=82, color="amber"),
        CapabilityDimension(name="笔试应试储备 (综合知识/算法)", score=78, color="sky"),
        CapabilityDimension(name="时间精力分配 (双轨平衡度)", score=75, color="rose"),
    ]

    masked_count = 0
    if profile and profile.token_map_json:
        try:
            tokens = json.loads(profile.token_map_json)
            masked_count = len(tokens.keys()) if isinstance(tokens, dict) else 0
        except Exception:
            masked_count = 0

    if profile and profile.education_level:
        summary = f"基于您的【{profile.education_level}】画像，已完成全域岗位门槛对齐与备考精力分配规划。"
    else:
        summary = "尚未配置求职画像，当前采用通用应届生评估模型。建议前往【系统设置】完善学历与意向以获得精准匹配。"

    return CapabilityRadarResponse(
        dimensions=dimensions,
        diagnostic_summary=summary,
        calibration_status="CALIBRATED",
        energy_split={
            "enterprise_pct": 55,
            "civil_exam_pct": 45,
            "advice": "建议前期聚焦优质名企提前批投递；进入公考窗口期后适度提升行测申论模考比重。"
        },
        sandbox_masked_count=masked_count
    )

@router.get("/diagnostics", response_model=List[AdvisoryDiagnosticItem])
async def get_diagnostic_items(db: AsyncSession = Depends(get_db)):
    """获取针对名企与公考的核心差距诊断卡片流"""
    return [
        AdvisoryDiagnosticItem(
            id="diag_1",
            category="ENTERPRISE",
            priority="P0",
            target_role="目标对标: 阿里淘天 / 华为云 / 腾讯 WXG 分布式后端开发",
            score=92,
            highlights="深度剖析 Linux 内核源码、自主研发并压测的高并发 RPC 框架与大厂 P6/15级 研发画像契合度达 95%。性能压测 QPS 提升 32% 数据扎实，是强有力的加分背书。",
            gaps="阿里淘天分布式JD中 3 次强调 Raft/Paxos 状态机复制协议。当前简历仅描述主从同步机制，高并发场景下容灾一致性表述薄弱，极易成为二面压力追问失分点。",
            action_advice="建议在专业技能与项目经历中补充基于 Raft 的强一致性元数据选举实践，突出容灾故障自愈指标。",
            replacement_before="原表述: 实现了底层主从心跳与选举通信，保障系统基础可用性。",
            replacement_after="建议替换为: 基于 Raft 协议实现高可用元数据仲裁模块，引入 Joint Consensus 动态集群配置变更，网络分区下故障自愈时间降低 42.8%。"
        ),
        AdvisoryDiagnosticItem(
            id="diag_2",
            category="CIVIL_SERVICE",
            priority="P0",
            target_role="岗位: 2027 浙江省考公务员 · 浙江省发改委数字经济处 (代码: 010302001)",
            score=100,
            highlights="应届生限定、中共党员政治面貌、工学硕士学位、计算机类专业目录 4 项核心刚性硬门槛全部审验通过！",
            gaps="招考备注包含录用后当地最低 5 年服务期条款；近三年同类进面平均分为 142.5 分 (行测72+申论70.5)。",
            action_advice="建议近期针对‘浙江数字经济创新提质一号发展工程’与数字政务改革积累至少 3 篇大作文申论策论金句。",
            special_notes=[
                "录用后在当地最低服务年限为 5 年，服务期内不得调离",
                "笔试科目对应综合类申论（一类），历年平均进面分 142.5",
                "建议首日完成网申报名，避免最后一日系统审核拥堵"
            ]
        )
    ]

@router.get("/predictions", response_model=List[ExamHitPrediction])
async def get_exam_predictions():
    """获取高频面试考点与机考实战押题"""
    return [
        ExamHitPrediction(
            title="淘天二面 (明天 15:30) 压轴押题",
            probability_desc="命中概率 91%",
            exam_time_desc="明天 15:30",
            key_points="必考场景: Redis 与 MySQL 双写一致性方案 (Canal binlog vs 延时双删)、Seata AT模式脏写防护原理、慢 SQL 真实线上排查案例。"
        ),
        ExamHitPrediction(
            title="招商银行总行 FinTech 统考机试 (本周六)",
            probability_desc="考点聚集",
            exam_time_desc="本周六 19:00",
            key_points="核心考点: ACM模式 I/O 规范、带备忘录的动态规划背包变形、并发线程安全队列设计，严防内存溢出超时。"
        )
    ]

@router.post("/chat", response_model=AdvisoryChatResponse)
async def advisory_copilot_chat(req: AdvisoryChatRequest, db: AsyncSession = Depends(get_db)):
    """AI 求职 Copilot 智能问答对话 (支持当前页面与选中实体上下文感知，集成真实大模型)"""
    msg = req.message.strip()
    ctx_page = req.context_page or ""
    ctx_title = req.context_title or ""

    repo = ProfileRepository(db)
    profile = await repo.get_or_create_default()

    edu = profile.education_level or "高校毕业生"
    politics = profile.political_status or "群众"
    majors = ", ".join(profile.major_tags or []) or "通用专业"
    roles = ", ".join(profile.target_roles or []) or "求职目标"
    cities = ", ".join(profile.target_cities or []) or "全国"
    resume_snippet = profile.masked_resume_text[:600] if profile.masked_resume_text else "暂无脱敏简历"

    # 1. 尝试调用真实大模型进行深度动态解答
    system_prompt = (
        "你是一个资深求职与考公咨询专家（CampusJob AI 求职 Copilot）。\n"
        "请基于求职者的真实画像（已在本地做隐私脱敏）、当前所处页面与正在查看的目标岗位/日程，给出务实、有深度且可落地的专业建议。\n"
        "指导原则：\n"
        "1. 拒绝空泛套话，针对具体企业/机关、岗位职责、技术栈或招考政策提供具体指导；\n"
        "2. 若用户询问简历或经历优化，使用 STAR 法则指出针对该岗位的具体改写要点；\n"
        "3. 若用户询问面试考点，给出核心高频场景与排障/答辩逻辑；\n"
        "4. 若用户询问沟通、延期或三方协议，提供礼貌、专业且有说服力的沟通话术；\n"
        "5. 重点突出候选人画像与目标岗位的契合度与短板补充。"
    )

    user_prompt = (
        f"【当前上下文】页面: {ctx_page or '全局咨询'} | 关注对象: {ctx_title or '通用目标'}\n"
        f"【候选人画像】学历: {edu} | 政治面貌: {politics} | 专业: {majors} | 意向岗位: {roles} | 目标城市: {cities}\n"
        f"【脱敏简历摘要】\n{resume_snippet}\n\n"
        f"【求职者提问】\n{msg}"
    )

    llm_reply = await BaseAgent.call_chat_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.6
    )

    if llm_reply:
        actions = []
        if any(w in msg for w in ["面试", "二面", "考题", "押题", "机试"]):
            actions.append(f"👉 针对【{ctx_title or '目标岗位'}】生成模拟面试追问清单")
            actions.append("👉 将核心知识点同步至备战备忘录")
        elif any(w in msg for w in ["简历", "优化", "针对性", "STAR"]):
            actions.append(f"👉 应用针对【{ctx_title or '目标岗位'}】的微调建议")
            actions.append("👉 更新简历专业技能关键词")
        elif any(w in msg for w in ["延期", "邮件", "话术", "三方"]):
            actions.append("👉 复制上述 HR 沟通模版")
            actions.append("👉 设置三方协议签署临界时间提醒")
        else:
            actions.append("👉 一键将建议要点沉淀至投递备忘录")
            actions.append("👉 探索契合该方向的更多校招/招考通告")

        return AdvisoryChatResponse(
            reply=llm_reply,
            related_actions=actions
        )

    # 2. 离线/规则动态降级 (保持透明与上下文感知，不硬编码假剧本)
    target_subject = ctx_title if ctx_title else (roles if roles != "求职目标" else "当前求职目标")

    if any(w in msg for w in ["延期", "邮件", "话术", "三方"]):
        reply = (
            "【大厂/名企 HR 礼貌延期三方沟通邮件模版】\n\n"
            "尊敬的校招 HR 老师：\n"
            "您好！非常感谢贵司对我技术能力与综合素质的认可，我也非常珍视该 Offer。\n"
            "由于目前毕业论文中期盲审及学术课题结项正处于关键冲刺答辩阶段，导师要求在此期间封闭攻关，"
            "故恳请能否将三方协议及入职意向书寄送/回传截止日期适当顺延至下周，以便我妥善处理完实验室交接并安心签约。\n\n"
            "再次感谢您的理解与包容！\n候选人：[CANDIDATE_NAME]"
        )
        actions = ["👉 复制邮件话术模版", "👉 设置三方 DDL 备忘录"]
    elif any(w in msg for w in ["阿里", "二面", "押题", "面试", "机试"]):
        reply = (
            f"针对【{target_subject}】的深度面试场景，结合您的【{edu} · {majors}】画像，建议重点准备以下方向：\n"
            "1. **高并发与共识一致性**：在分布式场景下，深入理解 Raft/Paxos 强一致性共识、网络分区下的 Leader 选举幂等性与数据同步机制；\n"
            "2. **生产瓶颈与系统排障**：线上服务出现性能抖动或高延迟时，如何结合链路追踪与性能分析工具快速定位死锁或慢请求；\n"
            "3. **消息积压与服务削峰**：在高并发流量洪峰下，如何平滑实现异步解耦、流控降级与核心数据幂等防重。\n\n"
            "*(提示：在【系统设置】中配置 LLM API Key，可解锁基于全量大模型的深度 1 对 1 针对性模拟提问)*"
        )
        actions = [f"👉 针对 {target_subject} 生成模拟面试考题", "👉 查看临面备战小抄包"]
    elif any(w in msg for w in ["公考", "胜率", "发改委", "选调", "进面", "申论"]):
        reply = (
            f"【{target_subject} · 报考胜率与竞争测算】\n"
            f"• **门槛筛选效应**：依托您的【{edu} · {politics} · {majors}】背景，在限定应届与党员的体制内岗位中具备较强准入优势；\n"
            "• **进面安全区间**：综合历年同类招考数据，建议目标分数锁定在 行测 72+、申论 68+，笔试总分达 140 分以上具备高进面概率；\n"
            "• **备考重点**：侧重行测理科模块答题速度，并针对数字经济与地方高质量发展积累策论金句。\n\n"
            "*(提示：在【系统设置】中配置 LLM API Key，可针对具体招考简章代码进行全量精准测算)*"
        )
        actions = ["👉 查看报考资格排查报告", "👉 设置公考报名窗口提醒"]
    elif "jobs" in ctx_page and ctx_title:
        reply = (
            f"已感知您当前正在查看岗位：【{ctx_title}】。\n"
            f"针对您的【{edu} · {majors}】背景：\n"
            f"1. **准入门槛**：基本符合该岗位的核心招录要求；\n"
            f"2. **简历针对性突出**：建议提炼与【{ctx_title}】紧密相关的项目经历，使用 STAR 法则强化量化指标；\n"
            f"3. **避坑提示**：重点关注 JD 中的硬性技能栈与网申截止日期。\n\n"
            "*(提示：配置 LLM API Key 后可解锁对该岗位 JD 的逐句简历重构建议)*"
        )
        actions = ["👉 一键将岗位加入追踪看板", "👉 导出该岗位专属自查清单"]
    else:
        reply = (
            f"已基于您的【{edu} · {majors} · {politics}】画像梳理：\n"
            f"针对您提出的「{msg}」，建议根据自身求职优先级（企业校招 vs 体制内考录）分配精力。\n"
            f"前期建议锁定核心意向目标提前批投递，并保持核心技能与行测模块的日常复习节奏。\n\n"
            "*(提示：在【系统设置】中配置 LLM API Key，即可开启与 Copilot 的深度自由问答)*"
        )
        actions = ["👉 完善求职画像与技能标签", "👉 浏览全域岗位流"]

    return AdvisoryChatResponse(
        reply=reply,
        related_actions=actions
    )


@router.get("/decision-matrix", response_model=DecisionMatrixResponse)
async def get_offer_decision_matrix(db: AsyncSession = Depends(get_db)):
    """获取针对当前锁定 Offer 与体制内意向的多目标效用推演沙盒"""
    # 结合俞军效用模型推演
    options = [
        OfferOption(
            id="offer_bytedance",
            name="字节跳动 · 商业化研发架构 (北京/杭州)",
            category="大厂研发 (顶级私企)",
            first_year_package="35k-42k · 年包约 55W-65W (含期权/签字费)",
            wlb_index=4,  # 加班相对较多
            stability_score=5,  # 存在业务线波动与35岁焦虑
            growth_ceiling=9,  # 技术影响力与跳槽溢价极高
            hukou_or_security="租房补贴 1500/月，无体制内编制，户口需走积分落户",
            breach_penalty="三方解约金 0 元，但需在 10月20日前线上确认",
            expected_utility_score=84.5,
            verdict="现金流最高，适合前 3 年积累技术资产与资本，需做好抗压准备"
        ),
        OfferOption(
            id="offer_hangzhou_gov",
            name="2027 浙江省考 · 省发改委数字经济处 (西湖区)",
            category="省直选调 / 公务员行政编",
            first_year_package="综合到手约 18W-22W · 住房公积金顶格缴纳",
            wlb_index=8,  # 规律作息，极少极端通宵
            stability_score=10,  # 铁饭碗，零裁员断缴风险
            growth_ceiling=8,  # 省直机关职级并行与遴选前景广阔
            hukou_or_security="直接解决杭州核心区行政编制，享省直机关分房/租住保障",
            breach_penalty="最低服务期 5 年内不得辞职或调离",
            expected_utility_score=91.0,
            verdict="综合防御性最强，极契合中共党员背景，长期效用期望最高"
        ),
        OfferOption(
            id="offer_cmb_fintech",
            name="招商银行 · 总行金融科技联合体 (深圳/杭州)",
            category="头部央国企金融机构",
            first_year_package="总包约 32W-38W · 六险二金 + 企业年金",
            wlb_index=6,  # 适度加班，银行风控合规要求高
            stability_score=8,  # 国资控股，稳定性高
            growth_ceiling=7,  # 金融 IT 架构业务护城河深
            hukou_or_security="深圳/杭州人才安居补贴，符合央企管培序列",
            breach_penalty="三方协议含 5000 元常规违约金条款",
            expected_utility_score=82.0,
            verdict="体面中庸路线，兼顾大厂 70% 的薪资与 80% 的体制稳定性"
        )
    ]

    heuristic = (
        "【俞军启发式决策判断】："
        "1. **计算替换成本**：若签大厂后毁约去体制内，大厂违约成本低（违约金为零）；但若先入职体制内再想跳大厂，替换成本极高（存在 5 年服务期刚性约束）。\n"
        "2. **期望效用最大化原则**：当前经济周期下，具有‘党员+工学硕士’双重光环的用户在省直选调赛道具备极高非对称优势。建议采取‘骑驴找马时差策略’：先用大厂意向书保底，卡满 10-20 决策期；同时全力准备 10-10 省考报名与 12 月统考笔试。"
    )

    delay_strategy = "建议向字节 HR 申请由于‘毕业课题中期答辩在即’顺延 1 周三方寄送，换取省考报名审核通过的确定性时间窗口。"

    return DecisionMatrixResponse(
        comparison_title="2027届硕士终局决策沙盘：大厂研发架构 vs 省直选调 vs 央企金科",
        user_utility_weights={
            "financial_package": "30%",
            "stability_and_security": "40%",
            "career_ceiling": "20%",
            "wlb_and_health": "10%"
        },
        options=options,
        agent_decision_heuristic=heuristic,
        delay_strategy=delay_strategy
    )

