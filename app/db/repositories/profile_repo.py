from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import UserPreferenceProfile
from app.schemas.profile import ProfileUpdate

class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_default(self) -> UserPreferenceProfile:
        stmt = select(UserPreferenceProfile).limit(1)
        res = await self.session.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            profile = UserPreferenceProfile()
            self.session.add(profile)
            await self.session.commit()
            await self.session.refresh(profile)
        return profile

    async def update(self, update_data: ProfileUpdate) -> UserPreferenceProfile:
        profile = await self.get_or_create_default()
        data_dict = update_data.model_dump(exclude_unset=True)
        for key, value in data_dict.items():
            if hasattr(profile, key) and key not in ("candidate_name", "university"):
                setattr(profile, key, value)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def save_sanitized_resume(
        self,
        raw_path: str,
        masked_text: str,
        encrypted_token_map: str,
        masked_name: str
    ) -> UserPreferenceProfile:
        profile = await self.get_or_create_default()
        profile.raw_resume_path = raw_path
        profile.masked_resume_text = masked_text
        profile.token_map_json = encrypted_token_map
        profile.candidate_name_masked = masked_name
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
