from pydantic import BaseModel
from typing import Optional


class StoreCreate(BaseModel):
    name: str
    address: Optional[str] = None


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
