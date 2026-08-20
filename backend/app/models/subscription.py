import enum
import uuid
from datetime import date, datetime

from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class PlanoNome(str, enum.Enum):
    GRATUITO = "gratuito"
    ESSENCIAL = "essencial"
    PROFISSIONAL = "profissional"
    EMPRESA = "empresa"
    REDE = "rede"


class StatusAssinatura(str, enum.Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100))
    stripe_price_id: Mapped[str | None] = mapped_column(String(100))
    valor_mensal: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)  # snapshot do valor recorrente, sincronizado do Stripe
    plano: Mapped[PlanoNome] = mapped_column(Enum(PlanoNome, name="plano_nome", values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=PlanoNome.GRATUITO, nullable=False)
    status: Mapped[StatusAssinatura] = mapped_column(Enum(StatusAssinatura, name="status_assinatura", values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=StatusAssinatura.ACTIVE, nullable=False)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    periodo_atual_fim: Mapped[date | None] = mapped_column(Date)  # proxima cobranca (Stripe: current_period_end)
    trial_fim: Mapped[date | None] = mapped_column(Date)
    cancelar_ao_fim_periodo: Mapped[bool] = mapped_column(default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    empresa = relationship("Empresa", back_populates="subscription")
    faturas = relationship("Fatura", back_populates="subscription", order_by="Fatura.criado_em.desc()")
