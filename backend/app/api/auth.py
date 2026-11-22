from fastapi import APIRouter, Depends

from ..dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id}
