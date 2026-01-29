
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, EmailStr

class AdminUserOut(BaseModel):
    id: str
    email: EmailStr
    is_admin: bool
    created_at: datetime | None = None

class DeleteUserResponse(BaseModel):
    id: str
    deleted: bool
