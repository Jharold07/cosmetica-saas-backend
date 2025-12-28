from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.inventory import MovementCreate, MovementResponse, StockResponse
from app.services.stock import get_stock

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/movements", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN"])),
):
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be > 0")

    # validar store pertenece al tenant
    store = db.execute(
        select(Store).where(Store.id == payload.store_id, Store.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=400, detail="Invalid store_id")

    # validar product pertenece al tenant
    product = db.execute(
        select(Product).where(Product.id == payload.product_id, Product.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=400, detail="Invalid product_id")

    movement_type = payload.movement_type

    if movement_type == "IN":
        direction = 1
    elif movement_type == "OUT":
        direction = -1
    else:  # ADJ
        if payload.direction not in (1, -1):
            raise HTTPException(status_code=400, detail="direction must be 1 or -1 for ADJ")
        direction = payload.direction

    # regla: no permitir OUT si no hay stock suficiente
    if movement_type == "OUT":
        current_stock = get_stock(db, current_user.tenant_id, payload.store_id, payload.product_id)
        if current_stock < payload.quantity:
            raise HTTPException(status_code=409, detail="Insufficient stock")

    movement = InventoryMovement(
        tenant_id=current_user.tenant_id,
        store_id=payload.store_id,
        product_id=payload.product_id,
        movement_type=movement_type,
        quantity=payload.quantity,
        direction=direction,
        note=payload.note,
        created_by=current_user.id,
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/stock", response_model=StockResponse)
def stock_by_product(
    store_id: int,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN", "VENDEDOR"])),
):
    # validar store y product dentro del tenant
    store = db.execute(
        select(Store.id).where(Store.id == store_id, Store.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=400, detail="Invalid store_id")

    product = db.execute(
        select(Product.id).where(Product.id == product_id, Product.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=400, detail="Invalid product_id")

    stock = get_stock(db, current_user.tenant_id, store_id, product_id)
    return {"store_id": store_id, "product_id": product_id, "stock": stock}

@router.get("/stock/by-barcode", response_model=StockResponse)
def stock_by_barcode(
    store_id: int,
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN", "VENDEDOR"])),
):
    store = db.execute(
        select(Store.id).where(Store.id == store_id, Store.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=400, detail="Invalid store_id")

    product_id = db.execute(
        select(Product.id).where(Product.tenant_id == current_user.tenant_id, Product.barcode == barcode.strip())
    ).scalar_one_or_none()
    if not product_id:
        raise HTTPException(status_code=404, detail="Product not found")

    stock = get_stock(db, current_user.tenant_id, store_id, int(product_id))
    return {"store_id": store_id, "product_id": int(product_id), "stock": stock}
