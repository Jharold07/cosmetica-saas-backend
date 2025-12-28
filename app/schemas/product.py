from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    category: Optional[str] = None
    barcode: str
    price: float
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]
    barcode: str
    price: float
    image_url: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
