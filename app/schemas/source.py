from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SourceBase(BaseModel):
    source_name: str = Field(..., description="信源名称")
    source_category: str = Field(default="CAMPUS", description="CAMPUS / BIG_TECH / CENTRAL_SOE / CIVIL_EXAM / CUSTOM")
    source_type: str = Field(default="PORTAL_RSS", description="CAMPUS_WEB / WECHAT_RSS / PORTAL_RSS / MANUAL")
    region_scope: Optional[str] = Field(default="全国", description="所属区域或省份")
    org_name: Optional[str] = Field(default=None, description="机构名称")
    feed_url: str = Field(..., description="抓取或 RSS 地址")
    cron_expr: str = Field(default="0 7,12,18 * * *", description="Cron 表达式")
    status: str = Field(default="ACTIVE", description="ACTIVE / DISABLED / ERROR")

class SourceCreate(SourceBase):
    is_preset: bool = False

class SourceUpdate(BaseModel):
    source_name: Optional[str] = None
    source_category: Optional[str] = None
    region_scope: Optional[str] = None
    feed_url: Optional[str] = None
    status: Optional[str] = None

class SourceResponse(SourceBase):
    id: int
    is_preset: bool
    last_crawled_at: Optional[datetime] = None
    last_error_msg: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SourceBatchStatusRequest(BaseModel):
    source_ids: Optional[List[int]] = None
    status: str = Field(..., description="ACTIVE 或 DISABLED")
    category: Optional[str] = None

class PresetSourceItem(BaseModel):
    key: str
    source_name: str
    source_category: str
    source_type: str
    region_scope: str
    org_name: str
    feed_url: str
    description: str
