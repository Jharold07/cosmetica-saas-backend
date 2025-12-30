from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from datetime import datetime


from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.store import Store
from app.models.user import User
from app.schemas.sales import SaleCreate, SaleResponse, SaleListItem
from app.services.stock import get_stock
from app.services.sales_number import generate_sale_number

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "VENDEDOR"])),
):
    if not payload.items or len(payload.items) == 0:
        raise HTTPException(status_code=400, detail="Sale must have at least 1 item")

    # validar store del tenant
    store_ok = db.execute(
        select(Store.id).where(Store.id == payload.store_id, Store.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    if not store_ok:
        raise HTTPException(status_code=400, detail="Invalid store_id")

    # regla: vendedor debe estar asignado a su tienda (si tiene store_id)
    if current_user.role_id is not None and current_user.store_id is not None:
        if current_user.store_id != payload.store_id and "ADMIN" not in ["ADMIN"]:
            # dejamos simple: si vendedor tiene store_id, no puede vender en otra tienda
            # (si quieres, lo hacemos por role_name real)
            raise HTTPException(status_code=403, detail="You cannot sell in another store")

    # validar pago
    if payload.payment_method == "YAPE" and (not payload.yape_operation_number or not payload.yape_operation_number.strip()):
        raise HTTPException(status_code=400, detail="yape_operation_number is required for YAPE")

    # Consolidar items por product_id (si repiten el mismo producto)
    merged = {}
    for it in payload.items:
        if it.quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity must be > 0")
        merged[it.product_id] = merged.get(it.product_id, 0) + it.quantity

    # validar productos y stock antes de guardar
    products = db.execute(
        select(Product).where(Product.tenant_id == current_user.tenant_id, Product.id.in_(list(merged.keys())))
    ).scalars().all()

    if len(products) != len(merged):
        raise HTTPException(status_code=400, detail="One or more products are invalid")

    # Stock check
    for p in products:
        available = get_stock(db, current_user.tenant_id, payload.store_id, p.id)
        required = merged[p.id]
        if available < required:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for product_id={p.id}")

    # calcular totales
    total = 0.0
    items_to_create: list[SaleItem] = []
    for p in products:
        qty = merged[p.id]
        unit_price = float(p.price)
        subtotal = unit_price * qty
        total += subtotal
        items_to_create.append(SaleItem(product_id=p.id, quantity=qty, unit_price=unit_price, subtotal=subtotal))

    sale = Sale(
        tenant_id=current_user.tenant_id,
        store_id=payload.store_id,
        user_id=current_user.id,
        number=generate_sale_number(db, current_user.tenant_id),
        payment_method=payload.payment_method,
        yape_operation_number=payload.yape_operation_number.strip() if payload.yape_operation_number else None,
        total=round(total, 2),
        is_voided=False,
    )
    sale.items = items_to_create

    db.add(sale)
    db.flush()  # para obtener sale.id sin commit aún

    # generar OUT en kardex
    for item in sale.items:
        mv = InventoryMovement(
            tenant_id=current_user.tenant_id,
            store_id=payload.store_id,
            product_id=item.product_id,
            movement_type="OUT",
            quantity=item.quantity,
            direction=-1,
            note=f"Sale {sale.number}",
            created_by=current_user.id,
        )
        db.add(mv)

@router.get("", response_model=list[SaleListItem])
def list_sales(
    store_id: int = Query(...),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    payment_method: str | None = Query(None),
    number: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "VENDEDOR"])),
):
    q = (
        select(Sale)
        .where(
            Sale.tenant_id == current_user.tenant_id,
            Sale.store_id == store_id,
        )
    )

    if payment_method:
        q = q.where(Sale.payment_method == payment_method)

    if number:
        q = q.where(Sale.number.ilike(f"%{number}%"))

    if date_from:
        q = q.where(Sale.created_at >= date_from)

    if date_to:
        q = q.where(Sale.created_at <= date_to)

    q = q.order_by(desc(Sale.created_at)).limit(limit).offset(offset)

    return db.execute(q).scalars().all()

@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "VENDEDOR"])),
):
    sale = db.execute(
        select(Sale)
        .where(Sale.id == sale_id, Sale.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    return sale

    db.commit()
    db.refresh(sale)
    return sale
