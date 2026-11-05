from sqlalchemy import Column, Float, String

from ..db.base import Base


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    quantity = Column(Float)
    unit = Column(String(50))
