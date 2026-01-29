from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import bad_request, unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.auth import TokenResponse, UserCreate, UserResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    email = payload.email.strip().lower()
    if not email:
        raise bad_request("Email is required")
    if not payload.password or len(payload.password) < 8:
        raise bad_request("Password must be at least 4 characters")

    existing = db.query(User).filter(User.email == email).one_or_none()
    if existing:
        raise bad_request("Email already registered")

    role = UserRole.user
    user = User(email=email, hashed_password=hash_password(payload.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    email = (form.username or "").strip().lower()
    user = db.query(User).filter(User.email == email).one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise unauthorized("Incorrect email or password")

    token = create_access_token(
        subject=user.id,
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
        extra={"role": user.role.value},
    )
    return TokenResponse(access_token=token, token_type="bearer")
