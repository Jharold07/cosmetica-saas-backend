from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN"])),
):
    product = Product(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        category=payload.category,
        barcode=payload.barcode.strip(),
        price=payload.price,
        image_url=payload.image_url,
        is_active=True,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Barcode already exists for this tenant")

    db.refresh(product)
    return product


@router.get("", response_model=list[ProductResponse])
def list_products(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN", "VENDEDOR"])),
):
    stmt = select(Product).where(Product.tenant_id == current_user.tenant_id)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Product.name.ilike(like)) | (Product.barcode.ilike(like)))

    products = db.execute(stmt.order_by(Product.id.desc())).scalars().all()
    return products


@router.get("/by-barcode/{barcode}", response_model=ProductResponse)
def get_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN", "VENDEDOR"])),
):
    product = db.execute(
        select(Product).where(
            Product.tenant_id == current_user.tenant_id,
            Product.barcode == barcode.strip(),
            Product.is_active == True,
        )
    ).scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ALMACEN"])),
):
    product = db.execute(
        select(Product).where(Product.id == product_id, Product.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.name is not None:
        product.name = payload.name
    if payload.category is not None:
        product.category = payload.category
    if payload.barcode is not None:
        product.barcode = payload.barcode.strip()
    if payload.price is not None:
        product.price = payload.price
    if payload.image_url is not None:
        product.image_url = payload.image_url
    if payload.is_active is not None:
        product.is_active = payload.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Barcode already exists for this tenant")

    db.refresh(product)
    return product
