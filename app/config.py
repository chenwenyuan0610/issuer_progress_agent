from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    notion_token: str
    notion_version: str = "2026-03-11"
    issuer_tracker_db_id: str
    issuer_history_db_id: str
    issuer_notes_db_id: str | None = None
    api_key: str = "change-me"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
