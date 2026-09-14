from typing import List, Optional
from pydantic import BaseModel, Field

class PositionItem(BaseModel):
    job_title: str = Field(..., description="岗位职称")
    job_category: str = Field(default="研发类", description="岗位大类")
    target_grad_year: Optional[str] = Field(default=None, description="面向毕业届数, 如 2027届")
    target_majors: List[str] = Field(default_factory=list, description="专业要求")
    degree_requirement: str = Field(default="硕士及以上", description="学历要求")
    work_locations: List[str] = Field(default_factory=list, description="工作地点")
    salary_range: Optional[str] = Field(default=None, description="薪资区间")
    responsibilities: Optional[str] = Field(default=None, description="岗位职责")
    requirements: Optional[str] = Field(default=None, description="任职要求")

class EventInfo(BaseModel):
    is_talk: bool = Field(default=False, description="是否包含专场宣讲会")
    talk_time: Optional[str] = Field(default=None, description="宣讲会时间, 如 2026-09-15 14:00:00")
    talk_location: Optional[str] = Field(default=None, description="宣讲会具体校区和教室地点")
    need_registration: bool = Field(default=False, description="是否需提前预约")

class ApplicationInfo(BaseModel):
    apply_deadline: Optional[str] = Field(default=None, description="网申截止时间, 如 2026-10-15 23:59:59")
    apply_link: Optional[str] = Field(default=None, description="网申链接或官方投递系统")
    referral_code: Optional[str] = Field(default=None, description="内推码")
    apply_method: Optional[str] = Field(default="官网网申", description="投递方式")

class EnterpriseJobPosting(BaseModel):
    """企业校招与名企直聘结构化抽取模型 (LLM Structured Output)"""
    posting_type: str = Field(default="ENTERPRISE")
    company_name: str = Field(..., description="规范企业名称")
    industry: Optional[str] = Field(default="互联网/高科技", description="行业分类")
    company_tier: Optional[str] = Field(default="头部名企", description="企业层级/性质")
    positions: List[PositionItem] = Field(default_factory=list, description="岗位列表")
    event_info: Optional[EventInfo] = Field(default_factory=EventInfo)
    application_info: Optional[ApplicationInfo] = Field(default_factory=ApplicationInfo)
