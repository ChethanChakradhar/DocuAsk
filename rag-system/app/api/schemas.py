from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    file_path: str
    page_count: int
    chunk_count: int
    chunk_ids: list[str]
    ingested_at: datetime


class UploadResponse(BaseModel):
    documents: list[DocumentSummary]


class ListDocumentsResponse(BaseModel):
    documents: list[DocumentSummary]


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    doc_id: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class SourceChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page: Optional[int] = None
    score: Optional[float] = None
    text: str


class AskResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    sources: list[SourceChunk]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
