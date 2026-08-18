import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class TipoAlerta(str, enum.Enum):
    VENCIMENTO_7_DIAS = "vencimento_7_dias"
    VENCIMENTO_3_DIAS = "vencimento_3_dias"
    VENCIMENTO_1_DIA = "vencimento_1_dia"
    VENCE_HOJE = "vence_hoje"
    VENCIDO = "vencido"
    ESTOQUE_BAIXO = "estoque_baixo"


class Alerta(Base):
    __tablename__ = "alertas"
    __table_args__ = (UniqueConstraint("lote_id", "tipo", name="uq_alerta_lote_tipo"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    lote_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("lotes.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[TipoAlerta] = mapped_column(Enum(TipoAlerta, name="tipo_alerta"), nullable=False, index=True)
    mensagem: Mapped[str] = mapped_column(String(500), nullable=False)
    data_alerta: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: now().date())
    lido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    ignorado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    produto = relationship("Produto")
    lote = relationship("Lote", back_populates="alertas")
