from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.sale import Sale


def generate_sale_number(db: Session, tenant_id: int) -> str:
    last_id = db.execute(
        select(func.coalesce(func.max(Sale.id), 0)).where(Sale.tenant_id == tenant_id)
    ).scalar_one()
    next_num = int(last_id) + 1
    return f"V-{next_num:06d}"
