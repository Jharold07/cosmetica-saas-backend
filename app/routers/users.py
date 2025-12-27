from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.security import hash_password
from app.models.role import Role
from app.models.store import Store
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


def _get_role_by_name(db: Session, tenant_id: int, role_name: str) -> Role:
    role = db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.name == role_name)
    ).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role_name")
    return role


def _validate_store(db: Session, tenant_id: int, store_id: int) -> Store:
    store = db.execute(
        select(Store).where(Store.id == store_id, Store.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=400, detail="Invalid store_id")
    return store


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    # Reglas: store_id requerido para VENDEDOR/ALMACEN
    role_name = payload.role_name.strip().upper()
    role = _get_role_by_name(db, current_user.tenant_id, role_name)

    if role_name in ["VENDEDOR", "ALMACEN"] and payload.store_id is None:
        raise HTTPException(status_code=400, detail="store_id is required for this role")

    if payload.store_id is not None:
        _validate_store(db, current_user.tenant_id, payload.store_id)

    # Email único por tenant
    exists = db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id, User.email == payload.email)
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Email already exists in this tenant")

    user = User(
        tenant_id=current_user.tenant_id,
        role_id=role.id,
        store_id=payload.store_id,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    users = db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id)
    ).scalars().all()
    return users


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"])),
):
    user = db.execute(
        select(User).where(User.id == user_id, User.tenant_id == current_user.tenant_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.role_name is not None:
        role_name = payload.role_name.strip().upper()
        role = _get_role_by_name(db, current_user.tenant_id, role_name)
        user.role_id = role.id

        # Si cambia a VENDEDOR/ALMACEN, store_id debe existir
        if role_name in ["VENDEDOR", "ALMACEN"] and (payload.store_id is None and user.store_id is None):
            raise HTTPException(status_code=400, detail="store_id is required for this role")

    if payload.store_id is not None:
        _validate_store(db, current_user.tenant_id, payload.store_id)
        user.store_id = payload.store_id

    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user
