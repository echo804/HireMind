"""App configuration from .env"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App config loaded from .env file"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    AI_BAILIAN_API_KEY: str = ""
    AI_BAILIAN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_DEFAULT_MODEL: str = "qwen3.5-flash"
    AI_DEFAULT_EMBEDDING_MODEL: str = "text-embedding-v3"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hiremind"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123456"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    STORAGE_BACKEND: str = "local"
    STORAGE_PATH: str = "./uploads"
    SESSION_SECRET_KEY: str = "change-me-to-random-string"
    ENCRYPTION_KEY: str = "32charrandomkeyforaikey"
    LOG_LEVEL: str = "INFO"


settings = Settings()
