from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.rag_service import RAGService


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    settings: Settings = get_settings()
    return RAGService(settings)
