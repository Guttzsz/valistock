import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class StatusLote(str, enum.Enum):
    ATIVO = "ativo"
    PROXIMO_VENCIMENTO = "proximo_vencimento"
    VENCIDO = "vencido"
    ESGOTADO = "esgotado"
    PERDIDO = "perdido"


class Lote(Base):
    __tablename__ = "lotes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    numero_lote: Mapped[str] = mapped_column(String(50), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    data_validade: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_entrada: Mapped[date] = mapped_column(Date, nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[StatusLote] = mapped_column(Enum(StatusLote, name="status_lote"), default=StatusLote.ATIVO, nullable=False, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    produto = relationship("Produto", back_populates="lotes")
    perdas = relationship("Perda", back_populates="lote")
    alertas = relationship("Alerta", back_populates="lote")
