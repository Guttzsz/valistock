import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class MotivoPerda(str, enum.Enum):
    PRODUTO_VENCIDO = "produto_vencido"
    PRODUTO_DANIFICADO = "produto_danificado"
    ARMAZENAMENTO_INADEQUADO = "armazenamento_inadequado"
    ERRO_DE_ESTOQUE = "erro_de_estoque"
    OUTRO = "outro"


class Perda(Base):
    __tablename__ = "perdas"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    lote_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("lotes.id", ondelete="SET NULL"), index=True)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[MotivoPerda] = mapped_column(Enum(MotivoPerda, name="motivo_perda"), nullable=False)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_perda: Mapped[date] = mapped_column(Date, nullable=False, default=lambda: now().date(), index=True)
    observacao: Mapped[str | None] = mapped_column(String(500))
    usuario_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    produto = relationship("Produto")
    lote = relationship("Lote", back_populates="perdas")
    usuario = relationship("Usuario")
