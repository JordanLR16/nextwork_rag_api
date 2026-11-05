from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_generator, verify_add_api_key
from ..schemas.query import AddKnowledgeRequest, QueryRequest
from ..services.query import answer_question
from .errors import internal_error, logger

router = APIRouter(tags=["query"])


@router.post("/query")
def query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    generate: Callable = Depends(get_generator),
):
    try:
        return answer_question(payload.q, payload.n_results, db, generate)
    except RuntimeError as exc:
        logger.error("Query dependency error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise internal_error("Query request failed")


@router.post("/add", dependencies=[Depends(verify_add_api_key)])
def add_knowledge(payload: AddKnowledgeRequest):
    raise HTTPException(status_code=501, detail="Use /recipes or /pantry for structured data")
