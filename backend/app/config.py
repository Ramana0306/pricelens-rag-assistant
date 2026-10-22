from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:password@localhost:5432/pricelens"
    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    session_ttl_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_page_chars: int = 50000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
