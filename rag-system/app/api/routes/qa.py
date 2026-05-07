from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_rag_service
from app.api.errors import api_error_from_exception
from app.api.schemas import AskRequest, AskResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> AskResponse:
    try:
        return rag_service.ask(question=payload.question, top_k=payload.top_k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise api_error_from_exception(
            exc,
            "I could not answer that question right now.",
        ) from exc
