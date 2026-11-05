import logging

from fastapi import HTTPException

logger = logging.getLogger("rag_api")


def internal_error(message: str) -> HTTPException:
    logger.exception(message)
    return HTTPException(status_code=500, detail="Internal server error")
