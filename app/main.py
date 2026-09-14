import os
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LITELLM_TELEMETRY"] = "False"
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.services.feed_market import init_preset_feeds
from app.services.seed_data import init_preset_jobs_and_tracker
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 自动初始化数据库表结构与索引
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. 注入四大类预设信源种子库与高质量演示招考与追踪数据
    async with AsyncSessionLocal() as session:
        await init_preset_feeds(session)
        await init_preset_jobs_and_tracker(session)

    # 3. 启动后台定时任务调度器 (RSS 抓取与早报推送)
    start_scheduler()

    yield

    # 优雅关闭
    stop_scheduler()
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.1.0",
    description="基于多 Agent 协同与本地隐私沙箱的高校校招与招考智能协同系统 API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API 统一路由
app.include_router(api_router)

web_dir = Path(__file__).resolve().parent.parent / "web"

# 统一 Web 应用程序路由（单体全栈应用工作台入口）
@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(web_dir / "dashboard.html")

@app.get("/jobs", include_in_schema=False)
async def serve_jobs():
    return FileResponse(web_dir / "jobs.html")

@app.get("/tracker", include_in_schema=False)
async def serve_tracker():
    return FileResponse(web_dir / "tracker.html")

@app.get("/calendar", include_in_schema=False)
async def serve_calendar():
    return FileResponse(web_dir / "calendar.html")

@app.get("/advisory", include_in_schema=False)
async def serve_advisory():
    return FileResponse(web_dir / "advisory.html")

@app.get("/settings", include_in_schema=False)
async def serve_settings():
    return FileResponse(web_dir / "settings.html")

# 挂载 Stitch 设计原型静态资源
stitch_dir = Path(__file__).resolve().parent.parent / "stitch_graduate_career_hub"
if stitch_dir.exists():
    app.mount("/stitch", StaticFiles(directory=str(stitch_dir), html=True), name="stitch")

# 挂载前端高保真工作台静态资源
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

