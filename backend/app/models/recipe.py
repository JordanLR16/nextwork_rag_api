from sqlalchemy import Column, ForeignKey, String, Text

from ..db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    ingredients = Column(Text, nullable=False, default="[]")
    instructions = Column(Text, nullable=False)
    substitutions = Column(Text, nullable=False, default="[]")
    tagline = Column(String(255))
    description = Column(Text)
    tags = Column(Text, nullable=False, default="[]")
