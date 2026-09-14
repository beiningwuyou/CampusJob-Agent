from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TrackerItemResponse(BaseModel):
    id: int
    job_id: int
    org_name: str
    job_title: str
    posting_type: str
    salary_desc: Optional[str] = None
    work_locations: List[str] = Field(default_factory=list)
    current_stage: str
    batch_title: Optional[str] = None
    resume_version: Optional[str] = None
    next_node_time: Optional[datetime] = None
    next_node_desc: Optional[str] = None
    is_critical: bool = False
    notes: Optional[str] = None
    match_score: int = 80
    apply_url: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TrackerKanbanResponse(BaseModel):
    metrics: dict
    stages: dict[str, List[TrackerItemResponse]]

class TrackerMoveStageRequest(BaseModel):
    new_stage: str
    note: Optional[str] = None
    next_node_time: Optional[datetime] = None
    next_node_desc: Optional[str] = None

class TrackerCreateRequest(BaseModel):
    job_id: int
    stage: str = "APPLIED"
    batch_title: Optional[str] = "秋招常规批次"
    resume_version: Optional[str] = "默认脱敏简历.pdf"
    notes: Optional[str] = None

class TrackerIngestRequest(BaseModel):
    raw_text: str = Field(..., description="邮件正文、通知短信或系统消息原始文本")

class ExtractedEvent(BaseModel):
    org_name: str
    job_title: Optional[str] = None
    event_type: str = Field(..., description="笔试测评/业务面试/HR沟通/意向Offer/已录用")
    mapped_stage: str = Field(..., description="APPLIED, WRITTEN_EXAM, INTERVIEW, REVIEW_CHECK, OFFER_ACCEPTED")
    scheduled_time_desc: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    location_or_link: Optional[str] = None
    access_code: Optional[str] = None
    summary: str
    matched_tracker_id: Optional[int] = None

class TrackerIngestResponse(BaseModel):
    success: bool
    event: ExtractedEvent
    matched_existing_record: bool
    confidence_score: int

class TrackerIngestConfirmRequest(BaseModel):
    tracker_id: Optional[int] = None
    org_name: str
    job_title: Optional[str] = None
    target_stage: str
    node_time: Optional[datetime] = None
    node_desc: Optional[str] = None
    notes: Optional[str] = None
    create_calendar_event: bool = True

class TrackerBatchImportItem(BaseModel):
    org_name: str
    job_title: str
    stage: str = "APPLIED"
    salary_desc: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class TrackerBatchImportRequest(BaseModel):
    items: List[TrackerBatchImportItem]
