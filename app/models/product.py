from sqlalchemy import String, Boolean, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    barcode: Mapped[str] = mapped_column(String(80), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # dinero: mejor Numeric
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tenant = relationship("Tenant", backref="products")

    __table_args__ = (
        # barcode único por empresa (tenant)
        UniqueConstraint("tenant_id", "barcode", name="uq_products_tenant_barcode"),
    )
