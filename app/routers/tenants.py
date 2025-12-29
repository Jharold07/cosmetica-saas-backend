from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantResponse
from app.core.dependencies import require_super_admin
from app.models.user import User
from app.models.role import Role
from app.schemas.user import TenantAdminCreate
from app.core.security import hash_password

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    exists = db.execute(select(Tenant).where(Tenant.name == name)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Tenant already exists")

    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

@router.post("/{tenant_id}/admins", status_code=status.HTTP_201_CREATED)
def create_tenant_admin(
    tenant_id: int,
    payload: TenantAdminCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_super_admin),
):
    # validar tenant exista
    tenant_exists = db.execute(select(Tenant.id).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if not tenant_exists:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # buscar rol ADMIN de ese tenant
    admin_role_id = db.execute(
        select(Role.id).where(Role.tenant_id == tenant_id, Role.name == "ADMIN")
    ).scalar_one_or_none()

    if not admin_role_id:
        raise HTTPException(status_code=400, detail="ADMIN role not found for this tenant")

    # email único
    email = payload.email.strip().lower()
    exists = db.execute(select(User.id).where(User.email == email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        tenant_id=tenant_id,
        role_id=admin_role_id,
        store_id=None,  # admin multi-tienda, luego elige/gestiona
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "tenant_id": user.tenant_id, "role": "ADMIN"}