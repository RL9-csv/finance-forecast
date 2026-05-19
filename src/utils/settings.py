"""환경 변수·설정 관리.

.env 파일을 자동 로딩하고 type-safe하게 접근.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """전역 설정.

    환경 변수에서 자동 로딩. .env 파일이 있으면 추가 로딩.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 데이터 소스 API
    alpha_vantage_key: str = ""
    fred_api_key: str = ""
    newsapi_key: str = ""
    dart_api_key: str = ""

    # LLM API
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # DB
    database_url: str = "postgresql://user:pass@localhost:5432/finance"
    duckdb_path: str = "data/finance.duckdb"

    # 모니터링
    sentry_dsn: str = ""
    wandb_api_key: str = ""

    # 알림
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # 환경
    environment: str = "development"
    log_level: str = "INFO"


# 싱글톤
settings = Settings()
