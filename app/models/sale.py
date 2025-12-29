from sqlalchemy import ForeignKey, String, Boolean, DateTime, func, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # número único por tenant (ej: V-000001)
    number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)  # CASH | YAPE
    yape_operation_number: Mapped[str | None] = mapped_column(String(60), nullable=True)

    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    is_voided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
