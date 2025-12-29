from pydantic import BaseModel
from typing import Optional, Literal


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
