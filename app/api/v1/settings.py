import zipfile
import io
from pathlib import Path
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.db.repositories.settings_repo import SettingsRepository
from app.schemas.settings import SystemSettingsResponse, SystemSettingsUpdateRequest

router = APIRouter(prefix="/settings", tags=["系统全局设置中心"])

@router.get("", response_model=SystemSettingsResponse)
async def get_system_settings(db: AsyncSession = Depends(get_db)):
    """获取系统 5 大 Tab 所有持久化配置与运行状态"""
    repo = SettingsRepository(db)
    config = await repo.get_or_create()

    data_path = Path(settings.DATA_DIR)
    db_path = str(data_path / "campusjob_agent_v1.db")
    posters_dir = data_path / "posters_cache"
    cache_size_mb = "5.2 MB"
    if posters_dir.exists():
        total_size = sum(f.stat().st_size for f in posters_dir.glob("**/*") if f.is_file())
        cache_size_mb = f"{round(total_size / (1024 * 1024), 1)} MB"


    return SystemSettingsResponse(
        id=config.id,
        crawl_interval_minutes=config.crawl_interval_minutes,
        request_timeout_seconds=config.request_timeout_seconds,
        retry_max_count=config.retry_max_count,
        wechat_proxy_mode=config.wechat_proxy_mode,
        llm_provider=config.llm_provider,
        llm_base_url=config.llm_base_url,
        has_llm_api_key=bool(config.llm_api_key_encrypted),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        sender_email=config.sender_email,
        has_smtp_auth_code=bool(config.smtp_auth_code_encrypted),
        receiver_email=config.receiver_email,
        daily_report_time=config.daily_report_time,
        report_modules=config.report_modules or ["TALK", "TOP_JOBS", "CIVIL_GOV", "URGENT_DDL"],
        quiet_mode_enabled=config.quiet_mode_enabled,
        master_key_masked="••••••••••••••••",
        database_path=db_path,
        posters_cache_size=cache_size_mb
    )

@router.put("", response_model=SystemSettingsResponse)
async def update_system_settings(
    data: SystemSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """保存并应用全局设置修改 (重置表单未保存状态)"""
    repo = SettingsRepository(db)
    await repo.update(data)
    return await get_system_settings(db)

@router.post("/cache-clean")
async def clean_temporary_cache():
    """清理历史图片与附件临时缓存"""
    data_path = Path(settings.DATA_DIR)
    posters_dir = data_path / "posters_cache"
    cleaned_bytes = 0
    if posters_dir.exists():
        for f in posters_dir.glob("**/*"):
            if f.is_file():
                cleaned_bytes += f.stat().st_size
                f.unlink(missing_ok=True)
    return {
        "status": "success",
        "message": f"已清理历史临时缓存，释放了 {round(cleaned_bytes / (1024 * 1024), 2)} MB 空间"
    }

@router.get("/backup")
async def export_full_backup():
    """全量导出数据库与配置 ZIP 备份"""
    data_path = Path(settings.DATA_DIR)
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        db_file = data_path / "campusjob_agent_v1.db"
        if db_file.exists():
            zf.write(db_file, arcname="campusjob_agent_v1.db")
    mem_zip.seek(0)
    return Response(
        content=mem_zip.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=campus_backup.zip"}
    )

