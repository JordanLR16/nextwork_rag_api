from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import PantryItem


def add(db: Session, data: dict, item_id: str, owner_id: str) -> PantryItem:
    item = PantryItem(id=item_id, **{**data, "owner_id": owner_id})
    db.add(item)
    return item


def list_all(db: Session, owner_id: str) -> list[PantryItem]:
    return db.execute(select(PantryItem).where(PantryItem.owner_id == owner_id)).scalars().all()


def search(db: Session, terms: list[str], limit: int, owner_id: str) -> list[PantryItem]:
    if not terms or limit <= 0:
        return []
    return db.execute(
        select(PantryItem)
        .where(PantryItem.owner_id == owner_id,
               or_(*(PantryItem.name.icontains(term, autoescape=True) for term in terms)))
        .order_by(PantryItem.name, PantryItem.id).limit(limit)
    ).scalars().all()


def serialize(item: PantryItem) -> dict:
    return {"id": item.id, "name": item.name, "quantity": item.quantity, "unit": item.unit}
