from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.store import Store
from app.models.user import User
from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse

router = APIRouter(prefix="/stores", tags=["Stores"])


# CREATE tienda (ADMIN)
@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    store = Store(
        tenant_id=current_user.tenant_id,
        name=payload.name,
        address=payload.address,
        is_active=True,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


# LIST tiernda por empresa  (ADMIN)
@router.get("", response_model=list[StoreResponse])
def list_stores(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    stores = db.execute(
        select(Store).where(Store.tenant_id == current_user.tenant_id)
    ).scalars().all()
    return stores


# UPDATE store (ADMIN)
@router.patch("/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    payload: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    store = db.execute(
        select(Store).where(
            Store.id == store_id,
            Store.tenant_id == current_user.tenant_id,
        )
    ).scalar_one_or_none()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if payload.name is not None:
        store.name = payload.name
    if payload.address is not None:
        store.address = payload.address
    if payload.is_active is not None:
        store.is_active = payload.is_active

    db.commit()
    db.refresh(store)
    return store
