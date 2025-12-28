from pydantic import BaseModel
from typing import Optional, Literal


class MovementCreate(BaseModel):
    store_id: int
    product_id: int
    movement_type: Literal["IN", "OUT", "ADJ"]
    quantity: int
    # solo para ADJ: +1 o -1 (para IN/OUT se ignora)
    direction: Optional[int] = 1
    note: Optional[str] = None


class MovementResponse(BaseModel):
    id: int
    store_id: int
    product_id: int
    movement_type: str
    quantity: int
    direction: int
    note: Optional[str]

    class Config:
        from_attributes = True


class StockResponse(BaseModel):
    store_id: int
    product_id: int
    stock: int
