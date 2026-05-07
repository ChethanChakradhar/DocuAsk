from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocuAsk"
    app_version: str = "1.0.0"
    environment: str = "dev"
    log_level: str = "INFO"
    app_passcode: str = Field(default="", alias="APP_PASSCODE")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_k: int = 6
    max_context_chars: int = 12000

    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    vector_store_dir: Path = Path("data/vector_store")
    metadata_path: Path = Path("data/documents.json")

    max_upload_size_mb: int = 25
    cors_allow_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        if not self.metadata_path.exists():
            self.metadata_path.write_text("{}", encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
