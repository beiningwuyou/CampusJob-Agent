import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.db.repositories.profile_repo import ProfileRepository
from app.schemas.profile import ProfileResponse, ProfileUpdate, ResumeSanitizePreview
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/profile", tags=["画像与隐私沙箱"])

@router.get("", response_model=ProfileResponse)
async def get_profile(db: AsyncSession = Depends(get_db)):
    """获取当前用户偏好画像与脱敏状态"""
    repo = ProfileRepository(db)
    profile = await repo.get_or_create_default()
    return ProfileResponse(
        id=profile.id,
        education_level=profile.education_level,
        grad_year=profile.grad_year,
        political_status=profile.political_status,
        major_tags=profile.major_tags or [],
        target_cities=profile.target_cities or [],
        job_interests=profile.job_interests or [],
        target_roles=profile.target_roles or [],
        exclude_keywords=profile.exclude_keywords or [],
        candidate_name_masked=profile.candidate_name_masked,
        has_resume=bool(profile.raw_resume_path),
        masked_resume_text=profile.masked_resume_text
    )

@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新求职意向与考公画像属性"""
    repo = ProfileRepository(db)
    profile = await repo.update(data)
    from app.services.matching_service import reevaluate_all_jobs_for_profile
    await reevaluate_all_jobs_for_profile(db, profile)
    return ProfileResponse(
        id=profile.id,
        education_level=profile.education_level,
        grad_year=profile.grad_year,
        political_status=profile.political_status,
        major_tags=profile.major_tags or [],
        target_cities=profile.target_cities or [],
        job_interests=profile.job_interests or [],
        target_roles=profile.target_roles or [],
        exclude_keywords=profile.exclude_keywords or [],
        candidate_name_masked=profile.candidate_name_masked,
        has_resume=bool(profile.raw_resume_path),
        masked_resume_text=profile.masked_resume_text
    )

@router.post("/upload-resume", response_model=ResumeSanitizePreview)
async def upload_and_sanitize_resume(
    file: UploadFile = File(...),
    candidate_name: str = Form(default=""),
    university: str = Form(default=""),
    db: AsyncSession = Depends(get_db)
):
    """上传 PDF 简历并在本地执行零泄露脱敏解析"""
    fname = file.filename.lower()
    if not (fname.endswith(".pdf") or fname.endswith(".txt")):
        raise HTTPException(status_code=400, detail="支持上传 PDF 或 TXT 格式简历文件")

    save_path = settings.resumes_dir / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text, masked_text, encrypted_tokens, token_map = ResumeService.extract_and_sanitize_pdf(
            pdf_path=save_path,
            candidate_name=candidate_name,
            university=university
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历脱敏解析失败: {str(e)}")

    masked_name_disp = candidate_name[:1] + "**" if candidate_name else "[已脱敏]"

    repo = ProfileRepository(db)
    await repo.save_sanitized_resume(
        raw_path=str(save_path),
        masked_text=masked_text,
        encrypted_token_map=encrypted_tokens,
        masked_name=masked_name_disp
    )

    return ResumeSanitizePreview(
        raw_char_count=len(raw_text),
        raw_text=raw_text,
        masked_text_preview=masked_text,
        tokens_masked=token_map
    )
