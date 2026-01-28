from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import User, UserRole
from app.db.session import SessionLocal


def seed_admin_if_configured() -> None:
    settings = get_settings()
    if not settings.seed_admin_email or not settings.seed_admin_password:
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.seed_admin_email).one_or_none()
        if existing:
            return
        admin = User(
            email=settings.seed_admin_email,
            hashed_password=hash_password(settings.seed_admin_password),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
    except IntegrityError:
        db.rollback()
    finally:
        db.close()
