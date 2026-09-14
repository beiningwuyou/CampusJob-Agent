from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.source import SourceCreate
from app.db.repositories.source_repo import SourceRepository

PRESET_FEEDS: List[Dict[str, str]] = [
    # 1. 高校就业专场 (985/211重点高校就业网)
    {
        "source_name": "浙江大学就业指导与服务中心",
        "source_category": "CAMPUS",
        "source_type": "CAMPUS_WEB",
        "region_scope": "浙江省",
        "org_name": "浙江大学",
        "feed_url": "https://career.zju.edu.cn/e-feed/news.xml",
        "cron_expr": "0 7,12,18 * * *",
    },
    {
        "source_name": "清华大学学生职业发展指导中心",
        "source_category": "CAMPUS",
        "source_type": "CAMPUS_WEB",
        "region_scope": "北京市",
        "org_name": "清华大学",
        "feed_url": "https://career.tsinghua.edu.cn/feed.xml",
        "cron_expr": "0 7,12,18 * * *",
    },
    {
        "source_name": "上海交通大学就业信息网",
        "source_category": "CAMPUS",
        "source_type": "CAMPUS_WEB",
        "region_scope": "上海市",
        "org_name": "上海交通大学",
        "feed_url": "https://career.sjtu.edu.cn/feed/campus.xml",
        "cron_expr": "0 7,12,18 * * *",
    },

    # 2. 知名互联网头部企业校招直聘
    {
        "source_name": "腾讯校园招聘官方动态",
        "source_category": "BIG_TECH",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "腾讯技术有限公司",
        "feed_url": "https://join.qq.com/feed/campus.xml",
        "cron_expr": "0 8,14 * * *",
    },
    {
        "source_name": "阿里巴巴校园招聘动态",
        "source_category": "BIG_TECH",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "阿里巴巴集团",
        "feed_url": "https://talent.alibaba.com/feed/campus.xml",
        "cron_expr": "0 8,14 * * *",
    },
    {
        "source_name": "华为全球校招专区",
        "source_category": "BIG_TECH",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "华为技术有限公司",
        "feed_url": "https://career.huawei.com/feed/freshman.xml",
        "cron_expr": "0 8,14 * * *",
    },
    {
        "source_name": "美团招聘官方资讯",
        "source_category": "BIG_TECH",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "美团",
        "feed_url": "https://zhaopin.meituan.com/feed/campus.xml",
        "cron_expr": "0 8,14 * * *",
    },

    # 3. 核心央国企人才直聘门户
    {
        "source_name": "国家电网人力资源招聘平台",
        "source_category": "CENTRAL_SOE",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "国家电网有限公司",
        "feed_url": "https://zhaopin.sgcc.com.cn/rss/notice.xml",
        "cron_expr": "0 7,13 * * *",
    },
    {
        "source_name": "中国移动人才招聘门户",
        "source_category": "CENTRAL_SOE",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "中国移动通信集团",
        "feed_url": "https://job.10086.cn/rss/campus.xml",
        "cron_expr": "0 7,13 * * *",
    },
    {
        "source_name": "中国石化毕业生招聘网",
        "source_category": "CENTRAL_SOE",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "中国石油化工集团",
        "feed_url": "https://job.sinopec.com/rss/graduates.xml",
        "cron_expr": "0 7,13 * * *",
    },

    # 4. 国家公务员及各省人事考试网 (公考/省考/事业单位)
    {
        "source_name": "国家公务员局专题招考资讯",
        "source_category": "CIVIL_EXAM",
        "source_type": "PORTAL_RSS",
        "region_scope": "全国",
        "org_name": "国家公务员局",
        "feed_url": "http://bm.scs.gov.cn/rss/gwy.xml",
        "cron_expr": "0 6,12,18 * * *",
    },
    {
        "source_name": "浙江省人事考试网招考公告",
        "source_category": "CIVIL_EXAM",
        "source_type": "PORTAL_RSS",
        "region_scope": "浙江省",
        "org_name": "浙江省人事考试院",
        "feed_url": "http://www.zjks.gov.cn/rss/gk.xml",
        "cron_expr": "0 6,12,18 * * *",
    },
    {
        "source_name": "广东省人事考试网考试录用专区",
        "source_category": "CIVIL_EXAM",
        "source_type": "PORTAL_RSS",
        "region_scope": "广东省",
        "org_name": "广东省人事考试局",
        "feed_url": "http://rsks.gd.gov.cn/rss/gwy.xml",
        "cron_expr": "0 6,12,18 * * *",
    },
    {
        "source_name": "北京市人力资源和社会保障局人事考试",
        "source_category": "CIVIL_EXAM",
        "source_type": "PORTAL_RSS",
        "region_scope": "北京市",
        "org_name": "北京市人事考试中心",
        "feed_url": "http://rsj.beijing.gov.cn/rss/zkgg.xml",
        "cron_expr": "0 6,12,18 * * *",
    },
]

async def init_preset_feeds(session: AsyncSession) -> int:
    """系统冷启动时自动注入四大类预设信源种子库"""
    repo = SourceRepository(session)
    inserted_count = 0
    for item in PRESET_FEEDS:
        existing = await repo.get_by_feed_url(item["feed_url"])
        if not existing:
            default_status = "DISABLED" if item.get("source_category") == "CAMPUS" else "ACTIVE"
            await repo.create(SourceCreate(
                source_name=item["source_name"],
                source_category=item["source_category"],
                source_type=item["source_type"],
                region_scope=item["region_scope"],
                org_name=item["org_name"],
                feed_url=item["feed_url"],
                cron_expr=item["cron_expr"],
                is_preset=True,
                status=default_status
            ))
            inserted_count += 1
    return inserted_count
