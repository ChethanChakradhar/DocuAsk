from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentRecord(BaseModel):
    doc_id: str
    filename: str
    file_path: str
    page_count: int
    chunk_count: int
    chunk_ids: list[str]
    ingested_at: datetime
