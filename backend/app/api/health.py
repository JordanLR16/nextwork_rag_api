from fastapi import APIRouter, Depends

from ..config import Settings
from ..dependencies import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)):
    return {"status": "ok", "database": settings.database_backend, "model": settings.model_name}
