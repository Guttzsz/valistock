import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class Reembolso(Base):
    __tablename__ = "reembolsos"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    fatura_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("faturas.id", ondelete="SET NULL"), index=True)
    stripe_refund_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(100))
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)

    empresa = relationship("Empresa")
    fatura = relationship("Fatura", back_populates="reembolsos")
