from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用基础配置
    APP_NAME: str = "CampusJob-Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # 数据路径
    DATA_DIR: str = "./data"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/campus_job.db"

    # LLM 配置
    LLM_MODEL: str = "deepseek/deepseek-chat"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.deepseek.com/v1"

    # SMTP 邮件配置
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_SSL: bool = True
    SMTP_SENDER_NAME: str = "CampusJob-Agent 求职助手"
    NOTIFICATION_RECIPIENT_EMAIL: str = ""

    # 定时调度
    DAILY_BRIEF_HOUR: int = 8
    DAILY_BRIEF_MINUTE: int = 0
    AUTO_CRAWL_INTERVAL_HOURS: int = 4

    @property
    def abs_data_dir(self) -> Path:
        p = Path(self.DATA_DIR)
        if not p.is_absolute():
            p = BASE_DIR / p
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def resumes_dir(self) -> Path:
        p = self.abs_data_dir / "resumes"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cache_dir(self) -> Path:
        p = self.abs_data_dir / "cache"
        p.mkdir(parents=True, exist_ok=True)
        return p

settings = Settings()
