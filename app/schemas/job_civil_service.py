from typing import List, Optional
from pydantic import BaseModel, Field

class CivilQualification(BaseModel):
    degree_requirement: str = Field(default="本科及以上", description="学历门槛")
    target_majors: List[str] = Field(default_factory=list, description="允许报考专业或学科大类")
    political_status_req: Optional[str] = Field(default="不限", description="政治面貌要求: 中共党员(含预备)/共青团员/不限")
    is_fresh_grad_only: bool = Field(default=False, description="是否仅限当年应届毕业生")
    service_year_limit: Optional[str] = Field(default=None, description="服务年限要求, 如 最低服务5年")
    special_notes: Optional[str] = Field(default=None, description="其他特殊报考限制或证书要求")

class CivilSchedule(BaseModel):
    apply_start_time: Optional[str] = Field(default=None, description="网上报名开始时间")
    apply_end_time: Optional[str] = Field(default=None, description="网上报名截止时间")
    payment_deadline: Optional[str] = Field(default=None, description="网上缴费确认截止时间")
    ticket_print_time: Optional[str] = Field(default=None, description="准考证打印时间")
    written_exam_time: Optional[str] = Field(default=None, description="公共科目笔试时间")

class CivilServicePosting(BaseModel):
    """公考/省考/选调生/事业单位招考公告与职位抽取模型"""
    posting_type: str = Field(default="CIVIL_EXAM")
    exam_name: str = Field(..., description="招考全称, 如 2027年浙江省各级机关单位考试录用公务员")
    authority_name: str = Field(..., description="招录机关/用人主管单位")
    department_name: Optional[str] = Field(default=None, description="用人具体处室/科室")
    post_name: str = Field(..., description="招考职位名称")
    post_code: Optional[str] = Field(default=None, description="职位代码")
    recruit_count: int = Field(default=1, description="招考计划招录人数")
    region_province: str = Field(default="全国", description="所属省份")
    region_city: Optional[str] = Field(default=None, description="所属地市")
    qualification: CivilQualification = Field(default_factory=CivilQualification)
    schedule: CivilSchedule = Field(default_factory=CivilSchedule)
    official_apply_url: Optional[str] = Field(default=None, description="官方报名入口网址")
