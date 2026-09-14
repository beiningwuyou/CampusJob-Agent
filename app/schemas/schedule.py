from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CalendarEventItem(BaseModel):
    id: str
    job_id: int
    title: str
    event_type: str = Field(..., description="TALK / APPLY_DDL / EXAM / REGISTRATION")
    color: str = Field(default="#3B82F6", description="HEX 颜色")
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_all_day: bool = False

class FastImportRequest(BaseModel):
    url: Optional[str] = Field(default=None, description="微信公众号或人事网链接")
    raw_text: Optional[str] = Field(default=None, description="手动粘贴的推文/海报纯文本")
    title_hint: Optional[str] = Field(default="手动导入招聘信息", description="标题提示")

class ConflictItem(BaseModel):
    conflict_id: str
    time_desc: str
    event_a_title: str
    event_a_score: int
    event_b_title: str
    event_b_score: int
    interval_minutes: int
    conflict_level: str  # CRITICAL / WARNING
    arbitration_verdict: str  # 俞军效用仲裁建议
    recommended_action: str  # 具体取舍行动

class CalendarConflictResponse(BaseModel):
    total_conflicts: int
    has_critical_conflict: bool
    conflicts: list[ConflictItem]

class EventPrepKitResponse(BaseModel):
    event_title: str
    event_time_desc: str
    location_or_link: str
    target_role: str
    match_score: int
    core_cheat_sheet: list[str]  # 1小时速记小抄/考前痛点
    star_project_highlights: str  # 对应简历项目自述要点
    interviewer_red_lines: list[str]  # 面试官/考官避坑红线
    urgent_todo: str  # 进场前立即执行
