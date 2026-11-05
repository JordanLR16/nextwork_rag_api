from sqlalchemy import Column, String, Text

from ..db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author_name = Column(String(255), nullable=False)
    ingredients = Column(Text, nullable=False, default="[]")
    instructions = Column(Text, nullable=False)
    substitutions = Column(Text, nullable=False, default="[]")
    tagline = Column(String(255))
    description = Column(Text)
    tags = Column(Text, nullable=False, default="[]")
