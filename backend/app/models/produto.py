import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (UniqueConstraint("empresa_id", "codigo_barras", name="uq_produto_empresa_codigo_barras"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    codigo_barras: Mapped[str | None] = mapped_column(String(50), index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(500))
    categoria: Mapped[str | None] = mapped_column(String(100), index=True)
    unidade_medida: Mapped[str] = mapped_column(String(20), default="UN", nullable=False)
    preco_custo: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    estoque_atual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    empresa = relationship("Empresa", back_populates="produtos")
    lotes = relationship("Lote", back_populates="produto", cascade="all, delete-orphan")
