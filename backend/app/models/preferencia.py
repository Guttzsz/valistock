import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now

WIDGETS_PADRAO = [
    "produtos_cadastrados",
    "proximos_vencimento",
    "vencidos",
    "valor_em_risco",
    "perdas_do_mes",
    "economia_potencial",
]


class PreferenciaNotificacao(Base):
    __tablename__ = "preferencias_notificacao"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    produtos_vencendo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    produtos_vencidos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    estoque_baixo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    novas_perdas: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relatorios: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avisos_administrativos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class PreferenciaDashboard(Base):
    __tablename__ = "preferencias_dashboard"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    widgets_ativos: Mapped[str] = mapped_column(Text, nullable=False, default="")  # JSON-encoded list, vazio = usa o padrao
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
