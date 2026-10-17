"""
config.py — application settings loaded from environment / .env file.
All secrets are optional here; the real values come from the environment.
Never print or log sensitive fields.
"""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


import os
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # FalkorDB
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379

    # CORS
    cors_origins: str = "http://localhost:3000"

    # LLM
    llm_mode: Literal["live", "fake"] = "live"
    llm_provider: Literal["groq", "openrouter", "gemini", "openai"] = "groq"
    llm_model: str = "qwen/qwen3.8-27b"
    llm_api_key: str = os.getenv("LLM_API_KEY", "")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
