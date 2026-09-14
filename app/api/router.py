from fastapi import APIRouter
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.feeds import router as feeds_router
from app.api.v1.profile import router as profile_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.tracker import router as tracker_router
from app.api.v1.advisory import router as advisory_router
from app.api.v1.settings import router as settings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard_router)
api_router.include_router(jobs_router)
api_router.include_router(feeds_router)
api_router.include_router(profile_router)
api_router.include_router(calendar_router)
api_router.include_router(tracker_router)
api_router.include_router(advisory_router)
api_router.include_router(settings_router)


@api_router.get("/health", tags=["系统监控"])
async def health_check():
    return {
        "status": "ok",
        "service": "CampusJob-Agent Backend",
        "version": "1.1.0",
        "sandbox_mode": "local_active"
    }
