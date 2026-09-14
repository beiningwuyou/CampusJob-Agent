from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class JobAdviceResponse(BaseModel):
    id: int
    job_id: int
    posting_type: str
    match_score: int
    match_level: str
    qualification_status: str
    highlights: List[str]
    gaps: List[str]
    action_advice: str
    interview_tips: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class JobListItemResponse(BaseModel):
    id: int
    posting_type: str
    org_name: str
    job_title: str
    post_code: Optional[str] = None
    category: str
    work_locations: List[str]
    degree_req: str
    major_reqs: List[str]
    political_req: Optional[str] = None
    is_fresh_only: bool
    salary_desc: Optional[str] = None
    talk_time: Optional[datetime] = None
    talk_location: Optional[str] = None
    apply_start: Optional[datetime] = None
    apply_ddl: Optional[datetime] = None
    exam_time: Optional[datetime] = None
    apply_url: Optional[str] = None
    is_archived: bool
    is_applied: bool
    created_at: datetime
    advice: Optional[JobAdviceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobListItemResponse):
    full_jd_json: dict[str, Any] = Field(default_factory=dict)
