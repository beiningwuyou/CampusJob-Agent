from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class ProfileBase(BaseModel):
    education_level: Optional[str] = Field(default=None, description="学历层次: 本科/硕士/博士")
    grad_year: Optional[int] = Field(default=None, description="毕业年份")
    political_status: Optional[str] = Field(default=None, description="政治面貌: 中共党员/中共预备党员/共青团员/群众")
    major_tags: List[str] = Field(default_factory=list, description="专业方向标签")
    target_cities: List[str] = Field(default_factory=list, description="意向城市/省份")
    job_interests: List[str] = Field(default_factory=list, description="意向大类")
    target_roles: List[str] = Field(default_factory=list, description="意向职位关键词")
    exclude_keywords: List[str] = Field(default_factory=list, description="排除黑名单")

class ProfileCreate(ProfileBase):
    candidate_name: Optional[str] = Field(default=None, description="真实姓名(仅在本地脱敏计算)")
    university: Optional[str] = Field(default=None, description="毕业院校(仅在本地脱敏计算)")

class ProfileUpdate(BaseModel):
    education_level: Optional[str] = None
    grad_year: Optional[int] = None
    political_status: Optional[str] = None
    major_tags: Optional[List[str]] = None
    target_cities: Optional[List[str]] = None
    job_interests: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    candidate_name: Optional[str] = None
    university: Optional[str] = None

class ProfileResponse(ProfileBase):
    id: int
    candidate_name_masked: Optional[str] = None
    has_resume: bool = False
    masked_resume_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ResumeSanitizePreview(BaseModel):
    raw_char_count: int
    raw_text: str = ""
    masked_text_preview: str
    tokens_masked: Dict[str, str] = Field(default_factory=dict)

