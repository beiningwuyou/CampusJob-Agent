from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import SystemSettingsConfig
from app.schemas.settings import SystemSettingsUpdateRequest

class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self) -> SystemSettingsConfig:
        stmt = select(SystemSettingsConfig).where(SystemSettingsConfig.id == 1)
        res = await self.session.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            config = SystemSettingsConfig(id=1)
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)
        return config

    async def update(self, data: SystemSettingsUpdateRequest) -> SystemSettingsConfig:
        config = await self.get_or_create()
        update_dict = data.model_dump(exclude_unset=True)

        # 处理敏感字段密文
        if "llm_api_key" in update_dict and update_dict["llm_api_key"]:
            config.llm_api_key_encrypted = f"enc_{update_dict['llm_api_key']}"
            del update_dict["llm_api_key"]

        if "smtp_auth_code" in update_dict and update_dict["smtp_auth_code"]:
            config.smtp_auth_code_encrypted = f"enc_{update_dict['smtp_auth_code']}"
            del update_dict["smtp_auth_code"]

        for k, v in update_dict.items():
            if hasattr(config, k):
                setattr(config, k, v)

        await self.session.commit()
        await self.session.refresh(config)
        return config
