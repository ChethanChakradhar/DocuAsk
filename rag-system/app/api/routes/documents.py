from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_rag_service
from app.api.errors import api_error_from_exception
from app.api.schemas import (
    DeleteDocumentResponse,
    DocumentSummary,
    ListDocumentsResponse,
    UploadResponse,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile] = File(...),
    rag_service: RAGService = Depends(get_rag_service),
) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required.")

    uploaded: list[DocumentSummary] = []

    for file in files:
        try:
            content = await file.read()
            record = rag_service.ingest_pdf(file.filename or "unknown.pdf", content)
            uploaded.append(DocumentSummary.model_validate(record.model_dump()))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            message = f"I could not add {file.filename or 'this PDF'} right now."
            raise api_error_from_exception(exc, message) from exc

    return UploadResponse(documents=uploaded)


@router.get("", response_model=ListDocumentsResponse)
def list_documents(
    rag_service: RAGService = Depends(get_rag_service),
) -> ListDocumentsResponse:
    docs = rag_service.list_documents()
    return ListDocumentsResponse(
        documents=[DocumentSummary.model_validate(d.model_dump()) for d in docs]
    )


@router.delete("/{doc_id}", response_model=DeleteDocumentResponse)
def delete_document(
    doc_id: str,
    rag_service: RAGService = Depends(get_rag_service),
) -> DeleteDocumentResponse:
    deleted = rag_service.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteDocumentResponse(deleted=True, doc_id=doc_id)
