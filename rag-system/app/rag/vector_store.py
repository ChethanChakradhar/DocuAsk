from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


class FaissVectorStore:
    def __init__(self, vector_store_dir: Path, embeddings: OpenAIEmbeddings) -> None:
        self.vector_store_dir = vector_store_dir
        self.embeddings = embeddings
        self._lock = threading.Lock()
        self._store: Optional[FAISS] = None
        self._load_if_exists()

    def _index_exists(self) -> bool:
        return (self.vector_store_dir / "index.faiss").exists() and (
            self.vector_store_dir / "index.pkl"
        ).exists()

    def _load_if_exists(self) -> None:
        if self._index_exists():
            self._store = FAISS.load_local(
                folder_path=str(self.vector_store_dir),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,
            )

    def _save(self) -> None:
        if self._store is not None:
            self._store.save_local(str(self.vector_store_dir))

    def add_documents(self, documents: list[Document], chunk_ids: list[str]) -> None:
        if not documents:
            return

        with self._lock:
            if self._store is None:
                self._store = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    ids=chunk_ids,
                )
            else:
                self._store.add_documents(documents=documents, ids=chunk_ids)
            self._save()

    def delete_by_chunk_ids(self, chunk_ids: list[str]) -> bool:
        if not chunk_ids:
            return True

        with self._lock:
            if self._store is None:
                return False
            deleted = self._store.delete(ids=chunk_ids)
            self._save()
            return bool(deleted)

    def similarity_search_with_score(self, query: str, k: int) -> list[tuple[Document, float]]:
        with self._lock:
            if self._store is None:
                return []
            return self._store.similarity_search_with_score(query=query, k=k)
