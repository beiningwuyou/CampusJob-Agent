import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import PrivacySanitizer
from app.schemas.job_enterprise import EnterpriseJobPosting
from app.schemas.job_civil_service import CivilServicePosting
from app.agents.structuring_agent import StructuringAgent
from app.agents.matching_agent import MatchingAgent
from app.db.models import UserPreferenceProfile
from app.services.mail_service import MailService

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.1.0"

@pytest.mark.asyncio
async def test_privacy_sanitizer():
    raw_resume = "我是张三，毕业于清华大学，手机号13800138000，邮箱zhangsan@test.com，身份证110101199003072391。"
    masked_text, token_map = PrivacySanitizer.sanitize_resume(
        raw_text=raw_resume,
        candidate_name="张三",
        university="清华大学"
    )

    # 验证敏感信息完全被占位符替换
    assert "张三" not in masked_text
    assert "13800138000" not in masked_text
    assert "zhangsan@test.com" not in masked_text
    assert "[CANDIDATE_NAME]" in masked_text
    assert "[PHONE_1]" in masked_text
    assert "[EMAIL_1]" in masked_text

    # 验证反向还原
    restored = PrivacySanitizer.restore_text(masked_text, token_map)
    assert "张三" in restored
    assert "13800138000" in restored

@pytest.mark.asyncio
async def test_dual_schema_structuring_enterprise():
    text = "【宣讲会】华为技术有限公司2027届全球校招启航！后端通用软件研发，宣讲地点玉泉永谦活动中心，网申截止2026-10-15。"
    parsed = await StructuringAgent.extract_posting(text, title_hint="华为校招宣讲")
    assert isinstance(parsed, EnterpriseJobPosting)
    assert "华为" in parsed.company_name

@pytest.mark.asyncio
async def test_dual_schema_structuring_civil_service():
    text = "2027年浙江省各级机关单位考试录用公务员公告。岗位代码0103001，招录机关省发改委，要求中共党员，仅限2027应届。"
    parsed = await StructuringAgent.extract_posting(text, title_hint="浙江省考招录公告")
    assert isinstance(parsed, CivilServicePosting)
    assert parsed.qualification.is_fresh_grad_only is True

@pytest.mark.asyncio
async def test_matching_agent_civil_service_qualification():
    profile = UserPreferenceProfile(
        grad_year=2027,
        political_status="共青团员",
        major_tags=["计算机科学与技术"]
    )

    # 测试政治面貌不满足的强拦截
    advice = MatchingAgent.evaluate_civil_service(
        post_name="数字化改革岗",
        authority_name="省委政法委",
        degree_req="硕士",
        target_majors=["计算机科学与技术"],
        political_req="中共党员",
        is_fresh_only=True,
        profile=profile
    )
    assert advice["qualification_status"] == "DISQUALIFIED"
    assert any("党员" in g for g in advice["gaps"])

@pytest.mark.asyncio
async def test_ics_generation():
    import datetime
    events = [{
        "title": "【宣讲会】腾讯公司",
        "start_time": datetime.datetime(2026, 9, 15, 14, 0),
        "location": "学生活动中心",
        "description": "技术专场"
    }]
    ics_bytes = MailService.generate_ics_calendar(events)
    assert b"BEGIN:VCALENDAR" in ics_bytes
    assert b"BEGIN:VEVENT" in ics_bytes
    assert b"\xe8\x85\xbe\xe8\xae\xaf" in ics_bytes or b"VCALENDAR" in ics_bytes

@pytest.mark.asyncio
async def test_tracker_and_advisory_and_settings_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. 验证 /tracker 看板与指标接口
        resp_tracker = await ac.get("/api/v1/tracker")
        assert resp_tracker.status_code == 200
        data_tracker = resp_tracker.json()
        assert "metrics" in data_tracker
        assert "stages" in data_tracker
        assert "APPLIED" in data_tracker["stages"]
        assert "WRITTEN_EXAM" in data_tracker["stages"]

        # 2. 验证 /advisory 能力雷达与押题
        resp_radar = await ac.get("/api/v1/advisory/radar")
        assert resp_radar.status_code == 200
        data_radar = resp_radar.json()
        assert len(data_radar["dimensions"]) == 6
        assert data_radar["calibration_status"] == "CALIBRATED"

        resp_chat = await ac.post("/api/v1/advisory/chat", json={"message": "针对阿里的二面场景，帮我押几道核心追问"})
        assert resp_chat.status_code == 200
        data_chat = resp_chat.json()
        assert "reply" in data_chat
        assert "Raft" in data_chat["reply"]

        # 3. 验证 /settings 5-Tab 系统设置与清理
        resp_settings = await ac.get("/api/v1/settings")
        assert resp_settings.status_code == 200
        data_settings = resp_settings.json()
        assert data_settings["crawl_interval_minutes"] == 30
        assert data_settings["llm_provider"] == "deepseek"

        resp_clean = await ac.post("/api/v1/settings/cache-clean")
        assert resp_clean.status_code == 200
        assert resp_clean.json()["status"] == "success"

@pytest.mark.asyncio
async def test_profile_update_and_dynamic_reevaluation():
    from app.db.session import AsyncSessionLocal
    from app.services.seed_data import init_preset_jobs_and_tracker
    async with AsyncSessionLocal() as session:
        await init_preset_jobs_and_tracker(session)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 验证获取当前画像
        resp = await ac.get("/api/v1/profile")
        assert resp.status_code == 200
        profile_data = resp.json()
        assert "education_level" in profile_data

        # 2. 修改画像为政治面貌="群众"
        update_payload = {
            "political_status": "群众",
            "education_level": "硕士",
            "grad_year": 2027
        }
        resp_update = await ac.put("/api/v1/profile", json=update_payload)
        assert resp_update.status_code == 200
        assert resp_update.json()["political_status"] == "群众"

        # 3. 验证全域岗位已动态重新推演: 浙江省定向选调(要求中共党员) 应被判定为 DISQUALIFIED 且 match_score == 0
        resp_jobs = await ac.get("/api/v1/jobs?limit=100")
        assert resp_jobs.status_code == 200
        jobs = resp_jobs.json()["items"]
        civil_job = next((j for j in jobs if j.get("posting_type") == "CIVIL_EXAM" and "党员" in (j.get("political_req") or "")), None)
        assert civil_job is not None, f"Available jobs: {[j.get('job_title') for j in jobs]}"
        assert civil_job["advice"] is not None
        assert civil_job["advice"]["qualification_status"] == "DISQUALIFIED"
        assert civil_job["advice"]["match_score"] == 0
        assert any("党员" in g for g in civil_job["advice"]["gaps"])

        # 4. 恢复画像为政治面貌="中共党员"，重新推演应恢复为 ELIGIBLE
        restore_payload = {
            "political_status": "中共党员",
            "education_level": "硕士",
            "grad_year": 2027,
            "major_tags": ["计算机科学与技术", "软件工程"]
        }
        resp_restore = await ac.put("/api/v1/profile", json=restore_payload)
        assert resp_restore.status_code == 200

        resp_jobs_restored = await ac.get("/api/v1/jobs")
        assert resp_jobs_restored.status_code == 200
        jobs_restored = resp_jobs_restored.json()["items"]
        civil_job_restored = next((j for j in jobs_restored if j.get("posting_type") == "CIVIL_EXAM" and "党员" in (j.get("political_req") or "")), None)
        assert civil_job_restored is not None
        assert civil_job_restored["advice"]["qualification_status"] == "ELIGIBLE"
        assert civil_job_restored["advice"]["match_score"] >= 80

        # 5. 清理测试产生的画像数据，恢复为纯净初始化状态
        await ac.put("/api/v1/profile", json={
            "political_status": None,
            "education_level": None,
            "grad_year": None,
            "major_tags": [],
            "target_cities": [],
            "target_roles": [],
            "exclude_keywords": []
        })

@pytest.mark.asyncio
async def test_tracker_csv_export():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/tracker/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment; filename=" in resp.headers.get("content-disposition", "")
        # 验证 UTF-8 BOM
        assert resp.content.startswith(b"\xef\xbb\xbf")
        text_content = resp.content.decode("utf-8-sig")
        assert "单位/企业名称" in text_content
        assert "当前阶段" in text_content

@pytest.mark.asyncio
async def test_feeds_crawl_and_toggle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 确保至少存在一个监控信源
        resp_add = await ac.post("/api/v1/feeds", json={
            "source_name": "清华大学就业网",
            "source_category": "CAMPUS",
            "source_type": "PORTAL_RSS",
            "feed_url": "https://career.tsinghua.edu.cn/rss"
        })
        assert resp_add.status_code == 200
        feed_id = resp_add.json()["id"]

        # 2. 触发单源即时抓取
        resp_crawl = await ac.post(f"/api/v1/feeds/{feed_id}/crawl")
        assert resp_crawl.status_code == 200
        data_crawl = resp_crawl.json()
        assert "抓取完成" in data_crawl["message"]

        # 3. 切换状态
        resp_toggle = await ac.patch(f"/api/v1/feeds/{feed_id}/toggle")
        assert resp_toggle.status_code == 200
        assert resp_toggle.json()["status"] in ["ACTIVE", "DISABLED"]

        # 4. 测试批量状态管理接口
        resp_batch = await ac.post("/api/v1/feeds/batch-status", json={
            "source_ids": [feed_id],
            "status": "DISABLED"
        })
        assert resp_batch.status_code == 200
        assert resp_batch.json()["success"] is True

        resp_batch_active = await ac.post("/api/v1/feeds/batch-status", json={
            "source_ids": [feed_id],
            "status": "ACTIVE"
        })
        assert resp_batch_active.status_code == 200
        assert resp_batch_active.json()["affected_count"] >= 1

        # 5. 测试删除信源接口
        resp_del = await ac.delete(f"/api/v1/feeds/{feed_id}")
        assert resp_del.status_code == 200
        assert resp_del.json()["success"] is True

@pytest.mark.asyncio
async def test_resume_upload_and_local_sanitize():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        sample_resume = "我是李四，毕业于浙江大学，联系电话13912345678，邮箱lisi@zju.edu.cn。求职后端开发。"
        files = {
            "file": ("resume_sample.txt", sample_resume.encode("utf-8"), "text/plain")
        }
        data = {
            "candidate_name": "李四",
            "university": "浙江大学"
        }
        resp = await ac.post("/api/v1/profile/upload-resume", files=files, data=data)
        assert resp.status_code == 200
        result = resp.json()
        assert "raw_text" in result
        assert "李四" in result["raw_text"]
        assert "masked_text_preview" in result
        assert "[CANDIDATE_NAME]" in result["masked_text_preview"]
        assert "[PHONE_1]" in result["masked_text_preview"]
        assert "李四" not in result["masked_text_preview"]
        assert "13912345678" not in result["masked_text_preview"]

        # 清理测试上传文件与重置简历字段
        from app.core.config import settings
        test_file = settings.resumes_dir / "resume_sample.txt"
        if test_file.exists():
            test_file.unlink()

        from app.db.session import AsyncSessionLocal
        from app.db.repositories.profile_repo import ProfileRepository
        async with AsyncSessionLocal() as session:
            repo = ProfileRepository(session)
            p = await repo.get_or_create_default()
            p.raw_resume_path = None
            p.masked_resume_text = None
            p.token_map_json = None
            p.candidate_name_masked = None
            await session.commit()

@pytest.mark.asyncio
async def test_fast_import_modal_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "raw_text": "【字节跳动2027校招】抖音架构团队直聘后端研发工程师，base北京/杭州/上海，薪资28k-45k，截止10月30日。"
        }
        resp = await ac.post("/api/v1/feeds/fast-import", json=payload)
        assert resp.status_code == 200
        res_data = resp.json()
        assert res_data["posting_type"] == "ENTERPRISE"
        assert res_data["job_id"] > 0
        assert "字节" in res_data["org_name"] or "研发" in res_data["job_title"]

@pytest.mark.asyncio
async def test_tracker_smart_ingest_and_confirm():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 测试智能嗅探解析面试通知短信
        sample_sms = "【腾讯招聘】同学你好，恭喜通过初筛，邀请你于明天 14:30 参加腾讯科技后端研发业务二面。腾讯会议：982-314-889，请提前5分钟进入。"
        ingest_resp = await ac.post("/api/v1/tracker/ingest", json={"raw_text": sample_sms})
        assert ingest_resp.status_code == 200
        data = ingest_resp.json()
        assert data["success"] is True
        assert "腾讯" in data["event"]["org_name"]
        assert data["event"]["mapped_stage"] == "INTERVIEW"
        assert "14:30" in data["event"]["scheduled_time_desc"]
        assert data["event"]["access_code"] == "982-314-889"

        # 2. 测试一键确认并持久化同步
        confirm_payload = {
            "tracker_id": data["event"]["matched_tracker_id"],
            "org_name": data["event"]["org_name"],
            "job_title": data["event"]["job_title"],
            "target_stage": data["event"]["mapped_stage"],
            "node_desc": data["event"]["summary"],
            "notes": "短信智能嗅探自动确认"
        }
        confirm_resp = await ac.post("/api/v1/tracker/ingest/confirm", json=confirm_payload)
        assert confirm_resp.status_code == 200
        confirm_data = confirm_resp.json()
        assert confirm_data["status"] == "success"
        assert confirm_data["target_stage"] == "INTERVIEW"

@pytest.mark.asyncio
async def test_offer_decision_matrix():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/advisory/decision-matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["options"]) >= 3
        assert any("字节" in opt["name"] for opt in data["options"])
        assert any("浙江省考" in opt["name"] or "发改委" in opt["name"] for opt in data["options"])
        assert "agent_decision_heuristic" in data
        assert "替换成本" in data["agent_decision_heuristic"]

@pytest.mark.asyncio
async def test_calendar_conflicts_and_prep_kit():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 测试日程冲突仲裁接口
        conflict_resp = await ac.get("/api/v1/calendar/conflicts")
        assert conflict_resp.status_code == 200
        c_data = conflict_resp.json()
        assert c_data["total_conflicts"] >= 1
        assert c_data["has_critical_conflict"] is True
        assert len(c_data["conflicts"]) > 0
        first_c = c_data["conflicts"][0]
        assert "效用仲裁" in first_c["arbitration_verdict"]
        assert first_c["conflict_level"] == "CRITICAL"
        assert first_c["event_a_score"] > 0

        # 2. 测试临考/临面备战小抄包
        kit_resp = await ac.get("/api/v1/calendar/prep-kit/ali_ddl_1")
        assert kit_resp.status_code == 200
        k_data = kit_resp.json()
        assert "阿里巴巴" in k_data["event_title"]
        assert len(k_data["core_cheat_sheet"]) >= 3
        assert "STAR" in k_data["urgent_todo"] or len(k_data["star_project_highlights"]) > 10
        assert len(k_data["interviewer_red_lines"]) >= 2

@pytest.mark.asyncio
async def test_context_aware_copilot_chat():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 测试跨页面上下文感知 (在 jobs 页面提问)
        req_payload = {
            "message": "请问我该怎么突出优势？",
            "context_page": "/jobs",
            "context_title": "华为终端BG 通用软件开发工程师"
        }
        resp = await ac.post("/api/v1/advisory/chat", json=req_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "华为终端BG" in data["reply"]
        assert len(data["related_actions"]) >= 1

        # 2. 测试三方延期沟通模板触发
        req_delay = {
            "message": "帮我写一封延期寄送三方协议给大厂HR的话术邮件",
            "context_page": "/advisory"
        }
        resp_delay = await ac.post("/api/v1/advisory/chat", json=req_delay)
        assert resp_delay.status_code == 200
        delay_data = resp_delay.json()
        assert "HR" in delay_data["reply"] or "三方" in delay_data["reply"]

@pytest.mark.asyncio
async def test_tracker_batch_import_and_seed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 测试批量导入投递
        import_payload = {
            "items": [
                {
                    "org_name": "快手科技",
                    "job_title": "大数据研发工程师",
                    "stage": "WRITTEN_EXAM",
                    "salary_desc": "28k*16薪",
                    "location": "北京",
                    "notes": "内推直通笔试"
                },
                {
                    "org_name": "中共浙江省委组织部",
                    "job_title": "数字经济处选调生",
                    "stage": "APPLIED",
                    "salary_desc": "统招选调",
                    "location": "杭州",
                    "notes": "资格初审中"
                }
            ]
        }
        resp = await ac.post("/api/v1/tracker/batch-import", json=import_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_count"] == 2

        # 2. 测试一键装填示范库
        seed_resp = await ac.post("/api/v1/tracker/seed-presets")
        assert seed_resp.status_code == 200
        assert "成功" in seed_resp.json()["message"]




