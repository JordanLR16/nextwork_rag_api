"""Map a verified external identity to a stable local application user."""

from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.exc import IntegrityError

from ..models import User


def resolve_user(db, issuer: str, subject: str) -> User:
    user_id = str(uuid5(NAMESPACE_URL, f"{issuer}\n{subject}"))
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, issuer=issuer, subject=subject, is_active=True)
        try:
            db.add(user)
            db.commit()
        except IntegrityError:
            # Concurrent first requests for the same identity may race.
            db.rollback()
            user = db.get(User, user_id)
            if user is None:
                raise
    return user
