import os
import pytest
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LITELLM_TELEMETRY"] = "False"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/campus_job_test.db"

from app.db.session import engine
from app.db.base import Base

@pytest.fixture(autouse=True)
async def init_test_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
