import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class EventoStripe(Base):
    """Controle de idempotencia: o Stripe pode reenviar o mesmo webhook mais de uma vez."""

    __tablename__ = "eventos_stripe"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    stripe_event_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    tipo_evento: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    processado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erro: Mapped[str | None] = mapped_column(String(1000))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
