from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.inventory_movement import InventoryMovement


def get_stock(db: Session, tenant_id: int, store_id: int, product_id: int) -> int:
    total = db.execute(
        select(func.coalesce(func.sum(InventoryMovement.quantity * InventoryMovement.direction), 0))
        .where(
            InventoryMovement.tenant_id == tenant_id,
            InventoryMovement.store_id == store_id,
            InventoryMovement.product_id == product_id,
        )
    ).scalar_one()
    return int(total)
