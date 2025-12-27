from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role_name: str  # "ADMIN" | "VENDEDOR" | "ALMACEN"
    store_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role_name: Optional[str] = None
    store_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role_id: int
    store_id: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True
