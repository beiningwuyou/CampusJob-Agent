from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class SystemSettingsResponse(BaseModel):
    id: int
    crawl_interval_minutes: int
    request_timeout_seconds: int
    retry_max_count: int
    wechat_proxy_mode: str

    llm_provider: str
    llm_base_url: str
    has_llm_api_key: bool
    temperature: float
    max_tokens: int

    smtp_host: str
    smtp_port: int
    sender_email: str
    has_smtp_auth_code: bool
    receiver_email: str
    daily_report_time: str
    report_modules: List[str]
    quiet_mode_enabled: bool

    master_key_masked: str
    database_path: str
    posters_cache_size: str

    model_config = ConfigDict(from_attributes=True)

class SystemSettingsUpdateRequest(BaseModel):
    crawl_interval_minutes: Optional[int] = None
    request_timeout_seconds: Optional[int] = None
    retry_max_count: Optional[int] = None
    wechat_proxy_mode: Optional[str] = None

    llm_provider: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    sender_email: Optional[str] = None
    smtp_auth_code: Optional[str] = None
    receiver_email: Optional[str] = None
    daily_report_time: Optional[str] = None
    report_modules: Optional[List[str]] = None
    quiet_mode_enabled: Optional[bool] = None

    master_key: Optional[str] = None
