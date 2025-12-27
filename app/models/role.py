from sqlalchemy import String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Cada empresa (tenant) define sus roles (en V1 serán los mismos, pero igual multi-tenant)
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    tenant = relationship("Tenant", backref="roles")

    __table_args__ = (
        # Evita roles duplicados por tenant (ej: dos ADMIN en la misma empresa)
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )
