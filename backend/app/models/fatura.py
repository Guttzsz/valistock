import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class StatusFatura(str, enum.Enum):
    PAGA = "paga"
    PENDENTE = "pendente"
    FALHOU = "falhou"
    REEMBOLSADA = "reembolsada"


class Fatura(Base):
    """Copia local de uma Stripe Invoice, para exibicao rapida no dashboard financeiro.
    O Stripe continua sendo a fonte oficial; esta tabela e sincronizada via webhook."""

    __tablename__ = "faturas"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("subscriptions.id", ondelete="SET NULL"), index=True)
    stripe_invoice_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    numero: Mapped[str | None] = mapped_column(String(50))
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    moeda: Mapped[str] = mapped_column(String(10), default="brl", nullable=False)
    status: Mapped[StatusFatura] = mapped_column(
        Enum(StatusFatura, name="status_fatura", values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    periodo_inicio: Mapped[date | None] = mapped_column(Date)
    periodo_fim: Mapped[date | None] = mapped_column(Date)
    url_fatura: Mapped[str | None] = mapped_column(String(500))
    url_pdf: Mapped[str | None] = mapped_column(String(500))
    pago_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    empresa = relationship("Empresa")
    subscription = relationship("Subscription", back_populates="faturas")
    reembolsos = relationship("Reembolso", back_populates="fatura")
