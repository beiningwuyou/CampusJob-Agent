from typing import List, Optional
from pydantic import BaseModel, Field

class CapabilityDimension(BaseModel):
    name: str
    score: int
    color: str = "emerald"

class CapabilityRadarResponse(BaseModel):
    dimensions: List[CapabilityDimension]
    diagnostic_summary: str
    calibration_status: str = "CALIBRATED"
    energy_split: dict
    sandbox_masked_count: int = 12

class AdvisoryDiagnosticItem(BaseModel):
    id: str
    category: str
    priority: str
    target_role: str
    score: int
    highlights: str
    gaps: str
    action_advice: str
    replacement_before: Optional[str] = None
    replacement_after: Optional[str] = None
    special_notes: Optional[List[str]] = None

class ExamHitPrediction(BaseModel):
    title: str
    probability_desc: str
    exam_time_desc: str
    key_points: str

class AdvisoryChatRequest(BaseModel):
    message: str
    job_id: Optional[int] = None
    context_page: Optional[str] = Field(default=None, description="当前所处页面，如 /jobs, /calendar, /tracker")
    context_title: Optional[str] = Field(default=None, description="当前聚焦的岗位或事件标题")
    history: List[dict] = Field(default_factory=list)

class AdvisoryChatResponse(BaseModel):
    reply: str
    related_actions: List[str] = Field(default_factory=list)

class OfferOption(BaseModel):
    id: str
    name: str
    category: str  # 大厂研发 / 地方选调 / 事业编制 / 央企
    first_year_package: str
    wlb_index: int  # 1-10分 (10最轻松稳定)
    stability_score: int  # 1-10分 (10最稳定)
    growth_ceiling: int  # 1-10分 (10发展空间最大)
    hukou_or_security: str  # 户口/编制/房补保障
    breach_penalty: str  # 违约金/限制条款
    expected_utility_score: float  # 俞军效用模型精算得分 (1-100)
    verdict: str

class DecisionMatrixResponse(BaseModel):
    comparison_title: str
    user_utility_weights: dict  # 收益、风险、舒适度权重
    options: List[OfferOption]
    agent_decision_heuristic: str  # 俞军启发式决策建议
    delay_strategy: str  # 拖延锁定时差博弈建议
