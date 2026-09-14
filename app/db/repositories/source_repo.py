from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SourceConfig, RawPost
from app.schemas.source import SourceCreate, SourceUpdate

class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_sources(self, category: Optional[str] = None) -> List[SourceConfig]:
        stmt = select(SourceConfig).order_by(SourceConfig.id.asc())
        if category and category != "ALL":
            stmt = stmt.where(SourceConfig.source_category == category)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_id(self, source_id: int) -> Optional[SourceConfig]:
        return await self.session.get(SourceConfig, source_id)

    async def get_by_feed_url(self, url: str) -> Optional[SourceConfig]:
        stmt = select(SourceConfig).where(SourceConfig.feed_url == url).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, data: SourceCreate) -> SourceConfig:
        source = SourceConfig(**data.model_dump())
        self.session.add(source)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def update(self, source_id: int, update_data: SourceUpdate) -> Optional[SourceConfig]:
        source = await self.get_by_id(source_id)
        if not source:
            return None
        for k, v in update_data.model_dump(exclude_unset=True).items():
            setattr(source, k, v)
        await self.session.commit()
        await self.session.refresh(source)
        return source

    async def delete(self, source_id: int) -> bool:
        source = await self.get_by_id(source_id)
        if not source:
            return False
        await self.session.delete(source)
        await self.session.commit()
        return True

    async def set_batch_status(
        self,
        status: str,
        source_ids: Optional[List[int]] = None,
        category: Optional[str] = None
    ) -> int:
        stmt = select(SourceConfig)
        if source_ids:
            stmt = stmt.where(SourceConfig.id.in_(source_ids))
        elif category and category != "ALL":
            stmt = stmt.where(SourceConfig.source_category == category)
        res = await self.session.execute(stmt)
        sources = res.scalars().all()
        for s in sources:
            s.status = status
        await self.session.commit()
        return len(sources)

    async def save_raw_post(
        self,
        source_id: int,
        source_category: str,
        source_url: str,
        title: str,
        extracted_text: str,
        raw_html: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> Optional[RawPost]:
        # 检查唯一性
        stmt = select(RawPost).where(RawPost.source_url == source_url).limit(1)
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        post = RawPost(
            source_id=source_id,
            source_category=source_category,
            source_url=source_url,
            title=title,
            raw_html=raw_html,
            extracted_text=extracted_text,
            image_urls=image_urls or [],
            process_status="PENDING"
        )
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post
