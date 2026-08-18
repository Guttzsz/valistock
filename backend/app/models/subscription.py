import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class PlanoNome(str, enum.Enum):
    GRATUITO = "gratuito"
    BASICO = "basico"
    PROFISSIONAL = "profissional"


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
    plano: Mapped[PlanoNome] = mapped_column(Enum(PlanoNome, name="plano_nome"), default=PlanoNome.GRATUITO, nullable=False)
    status: Mapped[StatusAssinatura] = mapped_column(Enum(StatusAssinatura, name="status_assinatura"), default=StatusAssinatura.ACTIVE, nullable=False)
    data_inicio: Mapped[date | None] = mapped_column(Date)
    data_fim: Mapped[date | None] = mapped_column(Date)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    empresa = relationship("Empresa", back_populates="subscription")
