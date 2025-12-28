from sqlalchemy import String, ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # IN, OUT, ADJ
    movement_type: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    # cantidad positiva siempre
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # para ADJ: +1 o -1 (IN/OUT siempre +1)
    direction: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", backref="inventory_movements")
    store = relationship("Store", backref="inventory_movements")
    product = relationship("Product", backref="inventory_movements")
    user = relationship("User", backref="inventory_movements")
