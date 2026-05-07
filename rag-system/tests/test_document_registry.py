from __future__ import annotations

from datetime import datetime, timezone

from app.services.document_registry import DocumentRegistry
from app.services.models import DocumentRecord


def test_upsert_and_list(tmp_path):
    metadata_path = tmp_path / "documents.json"
    registry = DocumentRegistry(metadata_path)

    record = DocumentRecord(
        doc_id="doc-1",
        filename="handbook.pdf",
        file_path="/tmp/handbook.pdf",
        page_count=4,
        chunk_count=12,
        chunk_ids=["doc-1:0", "doc-1:1"],
        ingested_at=datetime.now(timezone.utc),
    )
    registry.upsert(record)

    rows = registry.list_all()

    assert len(rows) == 1
    assert rows[0].doc_id == "doc-1"
    assert rows[0].filename == "handbook.pdf"
