from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from pydantic import Field


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int


class SaleCreate(BaseModel):
    store_id: int
    payment_method: Literal["CASH", "YAPE"]
    yape_operation_number: Optional[str] = None
    items: list[SaleItemCreate]


class SaleItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True

class SaleVoidRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)

class SaleResponse(BaseModel):
    id: int
    number: str
    store_id: int
    payment_method: str
    yape_operation_number: Optional[str]
    total: float
    items: list[SaleItemResponse]

    class Config:
        from_attributes = True

class SaleListItem(BaseModel):
    id: int
    number: str
    store_id: int
    payment_method: str
    yape_operation_number: Optional[str]
    total: float
    created_at: datetime

    class Config:
        from_attributes = True