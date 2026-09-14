from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index, Float
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class UserPreferenceProfile(Base, TimestampMixin):
    """用户偏好画像与本地脱敏配置表"""
    __tablename__ = "user_preference_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    education_level: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default=None)
    grad_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    political_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default=None)
    major_tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    target_cities: Mapped[List[str]] = mapped_column(JSON, default=list)
    job_interests: Mapped[List[str]] = mapped_column(JSON, default=list)
    target_roles: Mapped[List[str]] = mapped_column(JSON, default=list)
    exclude_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)

    # 本地脱敏与简历信息
    candidate_name_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_resume_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    masked_resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_map_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # AES 加密保存


class SourceConfig(Base, TimestampMixin):
    """信源配置表 (内置预设源与用户自定义源)"""
    __tablename__ = "source_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_category: Mapped[str] = mapped_column(String(30), default="CAMPUS")  # CAMPUS / BIG_TECH / CENTRAL_SOE / CIVIL_EXAM / CUSTOM
    source_type: Mapped[str] = mapped_column(String(30), default="PORTAL_RSS")  # CAMPUS_WEB / WECHAT_RSS / PORTAL_RSS / MANUAL
    region_scope: Mapped[Optional[str]] = mapped_column(String(50), default="全国")
    org_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    feed_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    cron_expr: Mapped[str] = mapped_column(String(50), default="0 7,12,18 * * *")
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE / DISABLED / ERROR
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    raw_posts = relationship("RawPost", back_populates="source", cascade="all, delete-orphan")


class RawPost(Base, TimestampMixin):
    """原始采集记录表"""
    __tablename__ = "raw_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_config.id", ondelete="CASCADE"), nullable=False)
    source_category: Mapped[str] = mapped_column(String(30), default="CAMPUS")
    source_url: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_urls: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    process_status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING / EXTRACTED / FAILED

    source = relationship("SourceConfig", back_populates="raw_posts")
    job_postings = relationship("JobPosting", back_populates="raw_post")


class JobPosting(Base, TimestampMixin):
    """标准化清洗后岗位与招考表 (企业与公考双模态)"""
    __tablename__ = "job_posting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_post_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("raw_post.id", ondelete="SET NULL"), nullable=True)

    posting_type: Mapped[str] = mapped_column(String(20), default="ENTERPRISE")  # ENTERPRISE / CIVIL_EXAM
    org_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # 企业名称或招考机关
    job_title: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    post_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 公考岗位代码
    category: Mapped[str] = mapped_column(String(50), default="综合类")
    work_locations: Mapped[List[str]] = mapped_column(JSON, default=list)
    degree_req: Mapped[str] = mapped_column(String(20), default="不限")
    major_reqs: Mapped[List[str]] = mapped_column(JSON, default=list)
    political_req: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_fresh_only: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_desc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 关键时间节点
    talk_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    talk_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    apply_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    apply_ddl: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    exam_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    apply_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 完整结构化 JSON
    full_jd_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    raw_post = relationship("RawPost", back_populates="job_postings")
    advice = relationship("JobMatchAdvice", back_populates="job", uselist=False, cascade="all, delete-orphan")
    track_record = relationship("ApplicationTrackRecord", back_populates="job", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_job_posting_type_org_ddl", "posting_type", "org_name", "apply_ddl"),
    )


class JobMatchAdvice(Base, TimestampMixin):
    """AI 契合度评分与投递/报考决策建议表"""
    __tablename__ = "job_match_advice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_posting.id", ondelete="CASCADE"), unique=True, nullable=False)
    posting_type: Mapped[str] = mapped_column(String(20), default="ENTERPRISE")

    match_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    match_level: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # HIGH / MEDIUM / LOW / REJECT
    qualification_status: Mapped[str] = mapped_column(String(20), default="ELIGIBLE")  # ELIGIBLE / WARN / DISQUALIFIED

    highlights: Mapped[List[str]] = mapped_column(JSON, default=list)
    gaps: Mapped[List[str]] = mapped_column(JSON, default=list)
    action_advice: Mapped[str] = mapped_column(Text, default="")
    interview_tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    job = relationship("JobPosting", back_populates="advice")


class ApplicationTrackRecord(Base, TimestampMixin):
    """求职全流程投递与招考跟踪表 (支撑 /tracker 五阶段看板)"""
    __tablename__ = "application_track_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_posting.id", ondelete="CASCADE"), unique=True, nullable=False)

    # 当前流程阶段:
    # 1. APPLIED (已网申/待初审)
    # 2. WRITTEN_EXAM (笔试阶段: 机试/行测)
    # 3. INTERVIEW (面试阶段: 专业/结构化)
    # 4. REVIEW_CHECK (体检/政审/差额考察)
    # 5. OFFER_ACCEPTED (意向录用/Offer/录用公示)
    # 6. ARCHIVED_REJECTED (已归档/未通过)
    current_stage: Mapped[str] = mapped_column(String(30), default="APPLIED", index=True)

    batch_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)     # 如 "提前批第1批次"
    resume_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 如 "v4.2_分布式重构.pdf"
    next_node_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True) # 下一关键时间点
    next_node_desc: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 如 "招行机考双机位"
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)                  # 是否处于临界待办(<48h)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)                  # 自定义备忘录
    history_logs: Mapped[List[dict]] = mapped_column(JSON, default=list)               # 流转审计日志

    job = relationship("JobPosting", back_populates="track_record")



class SystemSettingsConfig(Base, TimestampMixin):
    """系统全局配置与凭据持久化表 (支撑 /settings 5-Tab 设置)"""
    __tablename__ = "system_settings_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Tab 2: 抓取与代理策略
    crawl_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)
    request_timeout_seconds: Mapped[int] = mapped_column(Integer, default=15)
    retry_max_count: Mapped[int] = mapped_column(Integer, default=3)
    wechat_proxy_mode: Mapped[str] = mapped_column(String(50), default="LOCAL_RSSHUB")

    # Tab 3: 多 Agent 模型路由与凭据
    llm_provider: Mapped[str] = mapped_column(String(50), default="deepseek")
    llm_base_url: Mapped[str] = mapped_column(String(255), default="https://api.deepseek.com/v1")
    llm_api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)

    # Tab 4: 邮件与早报设置
    smtp_host: Mapped[str] = mapped_column(String(100), default="smtp.qq.com")
    smtp_port: Mapped[int] = mapped_column(Integer, default=465)
    sender_email: Mapped[str] = mapped_column(String(100), default="")
    smtp_auth_code_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receiver_email: Mapped[str] = mapped_column(String(100), default="")
    daily_report_time: Mapped[str] = mapped_column(String(10), default="08:00")
    report_modules: Mapped[List[str]] = mapped_column(JSON, default=lambda: ["TALK", "TOP_JOBS", "CIVIL_GOV", "URGENT_DDL"])
    quiet_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tab 5: 本地存储与安全
    master_key_hash: Mapped[str] = mapped_column(String(128), default="campus-local-master-key-2027")

