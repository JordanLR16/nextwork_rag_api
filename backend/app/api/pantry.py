from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_db, verify_add_api_key
from ..schemas.pantry import PantryItemIn
from ..services import pantry
from .errors import internal_error

router = APIRouter(tags=["pantry"])


@router.post("/pantry", dependencies=[Depends(verify_add_api_key)])
def add_pantry_item(payload: PantryItemIn, db: Session = Depends(get_db)):
    """Insert a pantry item, including when its name already exists."""
    try:
        return {"status": "success", "id": pantry.create_item(db, payload)}
    except Exception:
        raise internal_error("Add pantry failed")


@router.get("/pantry")
def list_pantry(db: Session = Depends(get_db)):
    try:
        items = pantry.list_items(db)
        return {"count": len(items), "items": items}
    except Exception:
        raise internal_error("List pantry failed")
