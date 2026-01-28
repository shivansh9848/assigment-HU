from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import forbidden, unauthorized
from app.core.security import decode_token
from app.db.models import User, UserRole
from app.db.session import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    settings = get_settings()
    try:
        payload = decode_token(token, secret=settings.jwt_secret, algorithm=settings.jwt_algorithm)
        user_id = payload.get("sub")
        if not user_id:
            raise unauthorized()
    except Exception:
        raise unauthorized()

    user = db.get(User, user_id)
    if not user:
        raise unauthorized()
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.admin:
        raise forbidden("Admin privileges required")
    return user
