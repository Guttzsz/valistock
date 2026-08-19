import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class TipoMovimentacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"
    PERDA = "perda"
    VENDA = "venda"


class MovimentacaoEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    lote_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("lotes.id", ondelete="SET NULL"), index=True)
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        Enum(TipoMovimentacao, name="tipo_movimentacao", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        index=True,
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    estoque_resultante: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str | None] = mapped_column(String(255))
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
