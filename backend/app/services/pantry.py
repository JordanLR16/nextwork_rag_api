import uuid

from sqlalchemy.orm import Session

from ..repositories import pantry
from ..schemas.pantry import PantryItemIn


def create_item(db: Session, payload: PantryItemIn) -> str:
    item_id = str(uuid.uuid4())
    try:
        item = pantry.add(db, payload.model_dump(), item_id)
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        raise
    return item_id


def list_items(db: Session) -> list[dict]:
    return [pantry.serialize(item) for item in pantry.list_all(db)]
