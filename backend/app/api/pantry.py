from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..schemas.pantry import PantryItemIn
from ..services import pantry
from .errors import internal_error

router = APIRouter(tags=["pantry"])


@router.post("/pantry")
def add_pantry_item(payload: PantryItemIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Insert a pantry item, including when its name already exists."""
    try:
        return {"status": "success", "id": pantry.create_item(db, payload, user.id)}
    except Exception:
        raise internal_error("Add pantry failed")


@router.get("/pantry")
def list_pantry(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        items = pantry.list_items(db, user.id)
        return {"count": len(items), "items": items}
    except Exception:
        raise internal_error("List pantry failed")
