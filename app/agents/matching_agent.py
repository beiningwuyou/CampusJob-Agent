import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent
from app.db.models import UserPreferenceProfile

class EnterpriseEvaluationResult(BaseModel):
    match_score: int = Field(ge=0, le=100, description="契合度综合评分 0-100")
    match_level: str = Field(description="HIGH / MEDIUM / LOW")
    qualification_status: str = Field(default="ELIGIBLE", description="ELIGIBLE / WARN / DISQUALIFIED")
    highlights: List[str] = Field(default_factory=list, description="契合亮点")
    gaps: List[str] = Field(default_factory=list, description="能力差距与短板")
    action_advice: str = Field(description="针对该岗位的具体简历改写建议")
    interview_tips: str = Field(description="针对该岗位面试重点与高频问题提示")

class CivilEvaluationResult(BaseModel):
    match_score: int = Field(ge=0, le=100, description="报考契合度与准入评估分 0-100")
    match_level: str = Field(description="HIGH / MEDIUM / LOW")
    qualification_status: str = Field(description="ELIGIBLE / WARN / DISQUALIFIED")
    highlights: List[str] = Field(default_factory=list, description="准入与优势亮点")
    gaps: List[str] = Field(default_factory=list, description="资格硬伤或潜在审核风险")
    action_advice: str = Field(description="报名与笔试备考行动建议")
    interview_tips: str = Field(description="面试结构化考察与重点政策指引")

class MatchingAgent(BaseAgent):
    """契合度推演与报考资格自查 Agent"""

    @classmethod
    async def evaluate_enterprise_job(
        cls,
        job_title: str,
        company_name: str,
        work_locations: List[str],
        degree_req: str,
        major_reqs: List[str],
        responsibilities: str,
        requirements: str,
        profile: UserPreferenceProfile
    ) -> Dict[str, Any]:
        """评估企业校招岗位的契合度及简历优化建议"""
        # 1. 尝试调用真实 LLM 进行深度多维推演
        system_prompt = (
            "你是一个资深企业校招评估专家。请根据候选人的求职画像（学历、专业、期望城市、期望岗位、技能栈）"
            "与目标企业岗位JD进行严谨深度比对，评估契合度，指出亮点、差距、简历具体改写方向和面试高频考点。"
            "必须针对该岗位的具体要求给出针对性落地建议，拒绝空洞套话。"
        )
        user_prompt = (
            f"【目标岗位】企业: {company_name} | 职位: {job_title} | 地点: {', '.join(work_locations or [])} | 学历要求: {degree_req}\n"
            f"专业要求: {', '.join(major_reqs or [])}\n"
            f"职责: {responsibilities}\n"
            f"要求: {requirements}\n\n"
            f"【候选人画像】学历: {profile.education_level or '未填写'} | 毕业年份: {profile.grad_year or '未填写'}\n"
            f"专业标签: {', '.join(profile.major_tags or [])}\n"
            f"意向城市: {', '.join(profile.target_cities or [])}\n"
            f"意向岗位: {', '.join(profile.target_roles or [])}\n"
            f"脱敏简历片段: {profile.masked_resume_text[:600] if profile.masked_resume_text else '无完整简历'}"
        )

        llm_res = await cls.call_structured_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=EnterpriseEvaluationResult
        )
        if llm_res:
            return llm_res.model_dump()

        # 2. 离线/规则动态降级评估 (保证不硬编码虚假数据，且严谨透明)
        return cls._fallback_evaluate_enterprise(
            job_title=job_title,
            company_name=company_name,
            work_locations=work_locations,
            degree_req=degree_req,
            major_reqs=major_reqs,
            responsibilities=responsibilities,
            requirements=requirements,
            profile=profile
        )

    @classmethod
    def _fallback_evaluate_enterprise(
        cls,
        job_title: str,
        company_name: str,
        work_locations: List[str],
        degree_req: str,
        major_reqs: List[str],
        responsibilities: str,
        requirements: str,
        profile: UserPreferenceProfile
    ) -> Dict[str, Any]:
        score = 60
        highlights = []
        gaps = []

        # 学历层次匹配
        if degree_req:
            user_edu = profile.education_level or ""
            if "博士" in degree_req and "博士" not in user_edu:
                score -= 20
                gaps.append(f"岗位要求博士学历，当前画像学历为 {user_edu or '未设定'}")
            elif "硕士" in degree_req and ("硕士" not in user_edu and "博士" not in user_edu):
                score -= 15
                gaps.append(f"岗位建议硕士学历，当前画像学历为 {user_edu or '未设定'}")
            else:
                score += 10
                highlights.append(f"学历层次符合要求 ({user_edu})")

        # 意向城市匹配
        target_cities = profile.target_cities or []
        if target_cities and work_locations:
            city_hit = any(city in " ".join(work_locations) for city in target_cities)
            if city_hit:
                score += 15
                highlights.append(f"工作地点在您的意向城市范围 ({', '.join(target_cities)})")
            else:
                gaps.append(f"工作地点在 {', '.join(work_locations)}，不在优先意向城市")

        # 专业与技能匹配
        user_majors = profile.major_tags or []
        combined_req = " ".join(major_reqs or []) + " " + requirements + " " + responsibilities
        if user_majors:
            major_hit = any(m in combined_req for m in user_majors)
            if major_hit:
                score += 15
                highlights.append(f"专业背景符合 ({', '.join(user_majors)})")
            else:
                score -= 10
                gaps.append(f"专业背景与JD首选要求不完全重合 ({', '.join(user_majors)})")

        # 意向岗位关键词
        target_roles = profile.target_roles or []
        if target_roles:
            role_hit = any(r in job_title or r in responsibilities for r in target_roles)
            if role_hit:
                score += 10
                highlights.append(f"核心职责与您的期望方向 ({', '.join(target_roles)}) 高度契合")

        score = max(min(score, 95), 20)
        level = "HIGH" if score >= 80 else ("MEDIUM" if score >= 65 else "LOW")

        # 动态根据当前公司与职位生成具体指导建议
        action_advice = (
            f"建议针对 {company_name} 的 {job_title} 岗位，重点提炼与【{job_title}】紧密相关的专业技能，"
            f"在简历项目中使用 STAR 法则量化核心技术难点与产出指标。"
        )
        interview_tips = (
            f"面试官大概率围绕 {job_title} 的核心职责（如系统可用性、核心架构设计、复杂业务排障）展开深挖，"
            f"请准备 1-2 个端到端的完整项目案例。"
        )

        return {
            "match_score": score,
            "match_level": level,
            "qualification_status": "ELIGIBLE",
            "highlights": highlights,
            "gaps": gaps,
            "action_advice": action_advice,
            "interview_tips": interview_tips
        }

    @classmethod
    def evaluate_civil_service(
        cls,
        post_name: str,
        authority_name: str,
        degree_req: str,
        target_majors: List[str],
        political_req: str,
        is_fresh_only: bool,
        profile: UserPreferenceProfile
    ) -> Dict[str, Any]:
        """公考编制硬性资格排查引擎"""
        qualification_status = "ELIGIBLE"
        highlights = []
        gaps = []

        # 关卡0: 学历层次硬性校验
        if degree_req:
            user_edu = profile.education_level or ""
            if "博士" in degree_req and "博士" not in user_edu:
                qualification_status = "DISQUALIFIED"
                gaps.append(f"该岗位要求博士研究生学历，当前画像学历为 {user_edu or '未设定'}")
            elif ("硕士" in degree_req or "研究生" in degree_req) and ("博士" not in user_edu and "硕士" not in user_edu):
                qualification_status = "DISQUALIFIED"
                gaps.append(f"该职位要求硕士研究生及以上学历，当前画像学历为 {user_edu or '未设定'}")
            else:
                highlights.append(f"学历层次符合 ({user_edu or '符合标准'})")

        # 关卡1: 应届生身份动态校验 (当前年份或下一届，非死板固化)
        if is_fresh_only:
            current_year = datetime.datetime.now().year
            # 考公招录通常在秋季启动次年届别，例如2026年秋招录2027应届生，毕业年份在 [current_year, current_year + 1] 均属于对应周期
            valid_grad_years = [current_year, current_year + 1]
            if profile.grad_year in valid_grad_years:
                highlights.append(f"应届生身份完全符合招录要求 ({profile.grad_year}届)")
            elif profile.grad_year is None:
                if qualification_status != "DISQUALIFIED":
                    qualification_status = "WARN"
                gaps.append("当前求职画像尚未填写毕业年份，无法确实验证应届生限制")
            else:
                qualification_status = "DISQUALIFIED"
                gaps.append(f"该职位仅限当年应届毕业生，您画像毕业年份为 {profile.grad_year}")

        # 关卡2: 政治面貌校验
        if political_req and "党员" in political_req:
            user_politics = profile.political_status or ""
            if "党员" in user_politics:
                highlights.append(f"政治面貌满足 ({user_politics})")
            else:
                qualification_status = "DISQUALIFIED"
                gaps.append(f"招考要求为中共党员(含预备)，您的当前身份为 {user_politics or '未填写/非党员'}")

        # 关卡3: 专业大类目录对照
        major_matched = False
        if not target_majors or any(w in " ".join(target_majors) for w in ["不限", "无限制"]):
            major_matched = True
            highlights.append("该职位无专业限制，可直接报考")
        else:
            for user_m in (profile.major_tags or []):
                for req_m in target_majors:
                    if user_m in req_m or req_m in user_m:
                        major_matched = True
                        break
            if major_matched:
                highlights.append(f"所学专业 ({', '.join(profile.major_tags or [])}) 命中招录专业大类")
            else:
                if qualification_status != "DISQUALIFIED":
                    qualification_status = "WARN"
                gaps.append(f"招考要求专业为 {', '.join(target_majors)}，建议在报名前电话咨询招录机关确认代码")

        match_score = 100 if qualification_status == "ELIGIBLE" else (60 if qualification_status == "WARN" else 0)

        action_advice = (
            f"建议密切关注 {authority_name} 的报名与资格初审时间窗口，提前准备在读证明与政治面貌证明材料；"
            f"复习侧重行测理科模块与申论公文规范表达。"
        )
        interview_tips = f"建议重点关注 {authority_name} 近期公开履职动态与相关领域重点政策文件。"

        return {
            "match_score": match_score,
            "match_level": "HIGH" if match_score >= 80 else "LOW",
            "qualification_status": qualification_status,
            "highlights": highlights,
            "gaps": gaps,
            "action_advice": action_advice,
            "interview_tips": interview_tips
        }
