#!/usr/bin/env python3
# ruff: noqa: E402
"""
CampusJob-Agent 演示数据一键初始化工具 (脱敏与开箱即用)
用于开源用户快速生成虚拟求职与投递看板数据，无需任何真实个人数据。
"""
import sys
import shutil
import asyncio
from pathlib import Path

# 将项目根目录加入模块搜索路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
import app.db.models  # noqa: F401
from app.services.seed_data import init_preset_jobs_and_tracker
from app.services.resume_service import ResumeService
from app.db.repositories.profile_repo import ProfileRepository
from app.schemas.profile import ProfileUpdate

async def main():
    print("=" * 60)
    print("🚀 正在初始化 CampusJob-Agent 演示环境...")
    print("=" * 60)

    # 1. 自动创建数据库表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表结构初始化成功！")

    # 2. 注入预设虚拟岗位与投递追踪数据
    async with AsyncSessionLocal() as session:
        await init_preset_jobs_and_tracker(session)
        print("✅ 成功同步典型双轨岗位与投递追踪卡片！")

        # 3. 设置虚拟脱敏求职画像
        repo = ProfileRepository(session)
        demo_profile = ProfileUpdate(
            grad_year=2027,
            education_level="硕士",
            political_status="中共党员",
            major_tags=["计算机科学与技术", "软件工程", "电子信息"],
            target_cities=["杭州", "北京", "上海", "深圳"],
            target_roles=["通用后端研发", "分布式存储", "数字化改革选调专岗", "FinTech管培生"],
            exclude_keywords=["销售", "客服", "劳务派遣"]
        )
        await repo.update(demo_profile)

        # 4. 注入虚拟候选人（张小明）的脱敏沙箱数据
        resumes_dir = project_root / "data" / "resumes"
        resumes_dir.mkdir(parents=True, exist_ok=True)
        demo_resume_file = resumes_dir / "演示候选人_2027届_计算机硕士_核心简历.txt"
        sample_source = project_root / "scripts" / "sample_resume.txt"

        if not demo_resume_file.exists() and sample_source.exists():
            shutil.copyfile(sample_source, demo_resume_file)

        if demo_resume_file.exists():
            raw_text, masked_text, encrypted_tokens, token_map = ResumeService.extract_and_sanitize_pdf(
                pdf_path=demo_resume_file,
                candidate_name="张小明",
                university="浙江大学"
            )
            await repo.save_sanitized_resume(
                raw_path=str(demo_resume_file),
                masked_text=masked_text,
                encrypted_token_map=encrypted_tokens,
                masked_name="张**"
            )
            print("✅ 成功配置演示脱敏求职画像与沙箱简历（张小明 · 2027届硕士 · 计算机技术）！")

    print("=" * 60)
    print("🎉 演示环境初始化完毕！现在您可以：")
    print("   1. 运行桌面原生端：./run_desktop.sh")
    print("   2. 运行 Web 浏览器端：uv run uvicorn app.main:app --reload")
    print("   3. 访问仪表盘：http://127.0.0.1:8000/dashboard")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
