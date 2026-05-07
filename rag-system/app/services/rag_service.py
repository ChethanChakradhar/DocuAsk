from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.api.schemas import AskResponse, SourceChunk
from app.core.config import Settings
from app.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.rag.vector_store import FaissVectorStore
from app.services.document_registry import DocumentRegistry
from app.services.models import DocumentRecord

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.registry = DocumentRegistry(settings.metadata_path)

        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        self.chat_model = ChatOpenAI(
            model=settings.openai_chat_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        self.vector_store = FaissVectorStore(settings.vector_store_dir, self.embeddings)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _ensure_openai_key(self) -> None:
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

    def list_documents(self) -> list[DocumentRecord]:
        return self.registry.list_all()

    def ingest_pdf(self, filename: str, payload: bytes) -> DocumentRecord:
        self._ensure_openai_key()

        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported.")

        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if len(payload) > max_bytes:
            raise ValueError(
                f"File too large. Max supported size is {self.settings.max_upload_size_mb} MB."
            )

        doc_id = str(uuid4())
        saved_path = self.settings.upload_dir / f"{doc_id}.pdf"
        saved_path.write_bytes(payload)

        try:
            pages = PyPDFLoader(str(saved_path)).load()
        except Exception as exc:
            if saved_path.exists():
                saved_path.unlink()
            raise ValueError(f"Could not parse PDF: {exc}") from exc

        if not pages:
            if saved_path.exists():
                saved_path.unlink()
            raise ValueError("PDF has no readable text content.")

        chunks = self.text_splitter.split_documents(pages)
        if not chunks:
            if saved_path.exists():
                saved_path.unlink()
            raise ValueError("No chunks were generated from this PDF.")

        prepared_chunks: list[Document] = []
        chunk_ids: list[str] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}:{idx}"
            page_value = chunk.metadata.get("page")
            page_number = int(page_value) + 1 if isinstance(page_value, int) else None

            metadata = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "filename": filename,
                "page": page_number,
            }
            prepared_chunks.append(
                Document(page_content=chunk.page_content, metadata=metadata)
            )
            chunk_ids.append(chunk_id)

        self.vector_store.add_documents(prepared_chunks, chunk_ids=chunk_ids)

        record = DocumentRecord(
            doc_id=doc_id,
            filename=filename,
            file_path=str(saved_path),
            page_count=len(pages),
            chunk_count=len(prepared_chunks),
            chunk_ids=chunk_ids,
            ingested_at=datetime.now(tz=timezone.utc),
        )
        self.registry.upsert(record)

        logger.info(
            "Ingested document",
            extra={
                "doc_id": doc_id,
                "document_filename": filename,
                "pages": len(pages),
                "chunks": len(prepared_chunks),
            },
        )

        return record

    def delete_document(self, doc_id: str) -> bool:
        record = self.registry.get(doc_id)
        if not record:
            return False

        self.vector_store.delete_by_chunk_ids(record.chunk_ids)

        path = Path(record.file_path)
        if path.exists():
            path.unlink()

        self.registry.delete(doc_id)
        return True

    def ask(self, question: str, top_k: Optional[int] = None) -> AskResponse:
        self._ensure_openai_key()

        k = top_k or self.settings.retrieval_k
        candidates = self.vector_store.similarity_search_with_score(query=question, k=k)

        if not candidates:
            return AskResponse(
                question=question,
                answer="I don't have enough information in the provided documents.",
                grounded=False,
                sources=[],
            )

        context_blocks: list[str] = []
        sources: list[SourceChunk] = []
        used_chars = 0

        for idx, (doc, score) in enumerate(candidates, start=1):
            text = " ".join(doc.page_content.split())
            source_label = (
                f"{doc.metadata.get('filename', 'unknown')}"
                f" p.{doc.metadata.get('page', '?')}"
            )
            block = f"[C{idx}]\nSource: {source_label}\nText: {text}"

            if context_blocks and (used_chars + len(block) > self.settings.max_context_chars):
                break

            context_blocks.append(block)
            used_chars += len(block)

            sources.append(
                SourceChunk(
                    chunk_id=str(doc.metadata.get("chunk_id", f"unknown:{idx}")),
                    doc_id=str(doc.metadata.get("doc_id", "unknown")),
                    filename=str(doc.metadata.get("filename", "unknown")),
                    page=doc.metadata.get("page"),
                    score=float(score),
                    text=text,
                )
            )

        prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context="\n\n".join(context_blocks),
        )

        completion = self.chat_model.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        answer = _to_text(completion.content)

        fallback = "i don't have enough information in the provided documents"
        grounded = bool(sources) and fallback not in answer.lower()

        return AskResponse(
            question=question,
            answer=answer,
            grounded=grounded,
            sources=sources,
        )


def _to_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()
    return str(content).strip()
