from sqlalchemy import Column, Float, ForeignKey, String

from ..db.base import Base


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Float)
    unit = Column(String(50))
