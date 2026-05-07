from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

from app.services.models import DocumentRecord


class DocumentRegistry:
    def __init__(self, metadata_path: Path) -> None:
        self.metadata_path = metadata_path
        self._lock = threading.Lock()
        if not self.metadata_path.exists():
            self.metadata_path.write_text("{}", encoding="utf-8")

    def _read_all(self) -> dict[str, dict]:
        with self.metadata_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data

    def _write_all(self, data: dict[str, dict]) -> None:
        with self.metadata_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True, indent=2, default=str)

    def upsert(self, record: DocumentRecord) -> None:
        with self._lock:
            data = self._read_all()
            data[record.doc_id] = record.model_dump(mode="json")
            self._write_all(data)

    def get(self, doc_id: str) -> Optional[DocumentRecord]:
        with self._lock:
            data = self._read_all()
            payload = data.get(doc_id)
        if payload is None:
            return None
        return DocumentRecord.model_validate(payload)

    def list_all(self) -> list[DocumentRecord]:
        with self._lock:
            data = self._read_all()
        records = [DocumentRecord.model_validate(v) for v in data.values()]
        records.sort(key=lambda x: x.ingested_at, reverse=True)
        return records

    def delete(self, doc_id: str) -> Optional[DocumentRecord]:
        with self._lock:
            data = self._read_all()
            payload = data.pop(doc_id, None)
            self._write_all(data)
        if payload is None:
            return None
        return DocumentRecord.model_validate(payload)
