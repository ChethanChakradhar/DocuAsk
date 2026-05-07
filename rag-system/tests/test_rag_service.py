from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.services.models import DocumentRecord
from app.services.rag_service import logger


def test_ingest_log_extra_does_not_use_reserved_filename(caplog):
    record = DocumentRecord(
        doc_id="doc-1",
        filename="cover-letter.pdf",
        file_path="data/uploads/doc-1.pdf",
        page_count=1,
        chunk_count=2,
        chunk_ids=["doc-1:0", "doc-1:1"],
        ingested_at=datetime.now(timezone.utc),
    )

    with caplog.at_level(logging.INFO):
        logger.info(
            "Ingested document",
            extra={
                "doc_id": record.doc_id,
                "document_filename": record.filename,
                "pages": record.page_count,
                "chunks": record.chunk_count,
            },
        )

    assert "Ingested document" in caplog.text
