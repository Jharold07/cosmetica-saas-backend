from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.role import Role

DEFAULT_ROLES = [
    ("ADMIN", "Acceso total a la empresa"),
    ("VENDEDOR", "Acceso solo a ventas"),
    ("ALMACEN", "Acceso a inventario y compras"),
]

def main():
    db = SessionLocal()
    try:
        tenants = db.execute(select(Tenant)).scalars().all()
        if not tenants:
            print("No tenants found. Create a tenant first.")
            return

        for t in tenants:
            for name, desc in DEFAULT_ROLES:
                exists = db.execute(
                    select(Role).where(Role.tenant_id == t.id, Role.name == name)
                ).scalar_one_or_none()
                if not exists:
                    db.add(Role(tenant_id=t.id, name=name, description=desc))
        db.commit()
        print("Roles seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
