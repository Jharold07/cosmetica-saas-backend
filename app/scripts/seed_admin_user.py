from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.role import Role
from app.models.user import User

ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASS = "Admin123!"  # cámbialo luego

def main():
    db = SessionLocal()
    try:
        tenant = db.execute(select(Tenant).order_by(Tenant.id.asc())).scalar_one_or_none()
        if not tenant:
            print("No tenants found. Create a tenant first.")
            return

        admin_role = db.execute(
            select(Role).where(Role.tenant_id == tenant.id, Role.name == "ADMIN")
        ).scalar_one_or_none()

        if not admin_role:
            print("ADMIN role not found for this tenant. Run seed_roles first.")
            return

        exists = db.execute(
            select(User).where(User.tenant_id == tenant.id, User.email == ADMIN_EMAIL)
        ).scalar_one_or_none()

        if exists:
            print("Admin user already exists.")
            return

        user = User(
            tenant_id=tenant.id,
            role_id=admin_role.id,
            store_id=None,  # ADMIN puede operar múltiples tiendas
            full_name="Admin Demo",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASS),
            is_active=True,
        )
        db.add(user)
        db.commit()

        print("Admin user created successfully.")
        print(f"Tenant: {tenant.name} (id={tenant.id})")
        print(f"Email: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASS}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
