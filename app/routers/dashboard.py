# app/routers/dashboard.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, date, time
from sqlalchemy import cast, Date
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.models.inventory_movement import InventoryMovement

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def _parse_date(d: str) -> datetime:
    # YYYY-MM-DD -> datetime inicio del día
    return datetime.combine(date.fromisoformat(d), time.min)

def _parse_date_end(d: str) -> datetime:
    # YYYY-MM-DD -> datetime fin del día
    return datetime.combine(date.fromisoformat(d), time.max)


def _start_of_today() -> datetime:
    return datetime.combine(date.today(), time.min)


def _start_of_month() -> datetime:
    today = date.today()
    return datetime.combine(date(today.year, today.month, 1), time.min)


@router.get("/summary")
def dashboard_summary(
    store_id: int | None = Query(default=None),
    low_stock_threshold: int = Query(default=5, ge=0, le=9999),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tenant_id = current_user.tenant_id

    # =========================
    # Ventas HOY (no anuladas)
    # =========================
    sales_today_stmt = (
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.tenant_id == tenant_id)
        .where(Sale.is_voided == False)
        .where(Sale.created_at >= _start_of_today())
    )
    if store_id is not None:
        sales_today_stmt = sales_today_stmt.where(Sale.store_id == store_id)

    sales_today = db.execute(sales_today_stmt).scalar_one()

    # =========================
    # Ventas del MES (no anuladas)
    # =========================
    sales_month_stmt = (
        select(func.coalesce(func.sum(Sale.total), 0))
        .where(Sale.tenant_id == tenant_id)
        .where(Sale.is_voided == False)
        .where(Sale.created_at >= _start_of_month())
    )
    if store_id is not None:
        sales_month_stmt = sales_month_stmt.where(Sale.store_id == store_id)

    sales_month = db.execute(sales_month_stmt).scalar_one()

    # =========================
    # Total productos (activos)
    # =========================
    products_total_stmt = (
        select(func.count(Product.id))
        .where(Product.tenant_id == tenant_id)
        .where(Product.is_active == True)
    )
    products_total = db.execute(products_total_stmt).scalar_one()

    # =========================
    # Stock total + stock crítico
    # stock = SUM(quantity * direction)
    # =========================
    stock_subq = (
        select(
            InventoryMovement.product_id.label("product_id"),
            func.coalesce(
                func.sum(InventoryMovement.quantity * InventoryMovement.direction), 0
            ).label("stock"),
        )
        .where(InventoryMovement.tenant_id == tenant_id)
        .group_by(InventoryMovement.product_id)
    )
    if store_id is not None:
        stock_subq = stock_subq.where(InventoryMovement.store_id == store_id)

    stock_subq = stock_subq.subquery()

    # Stock total (unidades)
    stock_total_stmt = select(func.coalesce(func.sum(stock_subq.c.stock), 0))
    stock_total_units = db.execute(stock_total_stmt).scalar_one()

    # Conteo de productos con stock <= threshold (solo activos)
    low_stock_stmt = (
        select(func.count(Product.id))
        .select_from(Product)
        .outerjoin(stock_subq, stock_subq.c.product_id == Product.id)
        .where(Product.tenant_id == tenant_id)
        .where(Product.is_active == True)
        .where(func.coalesce(stock_subq.c.stock, 0) <= low_stock_threshold)
    )
    low_stock_count = db.execute(low_stock_stmt).scalar_one()

    return {
        "sales_today": float(sales_today),
        "sales_month": float(sales_month),
        "products_total": int(products_total),
        "stock_total_units": int(stock_total_units),
        "low_stock_count": int(low_stock_count),
    }

@router.get("/top-products")
def top_products(
    store_id: int | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    stmt = (
        select(
            Product.id.label("product_id"),
            Product.name.label("name"),
            func.coalesce(func.sum(SaleItem.quantity), 0).label("quantity"),
            func.coalesce(func.sum(SaleItem.subtotal), 0).label("total"),
        )
        .select_from(SaleItem)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .join(Product, Product.id == SaleItem.product_id)
        .where(Sale.tenant_id == current_user.tenant_id)
        .where(Sale.is_voided == False)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
    )

    if store_id is not None:
        stmt = stmt.where(Sale.store_id == store_id)

    if date_from:
        stmt = stmt.where(Sale.created_at >= _parse_date(date_from))
    if date_to:
        stmt = stmt.where(Sale.created_at <= _parse_date_end(date_to))

    rows = db.execute(stmt).mappings().all()
    return list(rows)



@router.get("/sales-series")
def sales_series(
    period: str = Query(default="day", pattern="^(day|hour|month)$"),
    store_id: int | None = Query(default=None),
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if period == "day":
        label_expr = cast(Sale.created_at, Date)  # 2026-01-02
    elif period == "month":
        label_expr = func.to_char(Sale.created_at, "YYYY-MM")
    else:  # hour
        label_expr = func.to_char(Sale.created_at, "YYYY-MM-DD HH24:00")

    stmt = (
        select(
            label_expr.label("label"),
            func.coalesce(func.sum(Sale.total), 0).label("total"),
        )
        .where(Sale.tenant_id == current_user.tenant_id)
        .where(Sale.is_voided == False)
        .group_by(label_expr)
        .order_by(label_expr)
    )

    if store_id is not None:
        stmt = stmt.where(Sale.store_id == store_id)

    if date_from:
        stmt = stmt.where(Sale.created_at >= _parse_date(date_from))
    if date_to:
        stmt = stmt.where(Sale.created_at <= _parse_date_end(date_to))

    rows = db.execute(stmt).mappings().all()
    return list(rows)
