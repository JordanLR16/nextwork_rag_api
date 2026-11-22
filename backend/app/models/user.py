from sqlalchemy import Boolean, Column, String, UniqueConstraint

from ..db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("issuer", "subject", name="uq_users_identity"),)

    id = Column(String(50), primary_key=True)
    issuer = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
