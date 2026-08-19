import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class TipoCampoPersonalizado(str, enum.Enum):
    TEXTO = "texto"
    NUMERO = "numero"
    DATA = "data"
    SELECAO = "selecao"
    BOOLEANO = "booleano"


class CampoPersonalizado(Base):
    __tablename__ = "campos_personalizados"
    __table_args__ = (UniqueConstraint("empresa_id", "nome", name="uq_campo_personalizado_empresa_nome"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoCampoPersonalizado] = mapped_column(
        Enum(TipoCampoPersonalizado, name="tipo_campo_personalizado", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    obrigatorio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opcoes: Mapped[str | None] = mapped_column(Text)  # JSON-encoded list of strings, usado quando tipo == selecao
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    valores = relationship("ValorCampoPersonalizado", back_populates="campo", cascade="all, delete-orphan")


class ValorCampoPersonalizado(Base):
    __tablename__ = "valores_campos_personalizados"
    __table_args__ = (UniqueConstraint("campo_id", "produto_id", name="uq_valor_campo_produto"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    campo_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("campos_personalizados.id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False, index=True)
    valor: Mapped[str | None] = mapped_column(Text)

    campo = relationship("CampoPersonalizado", back_populates="valores")
    produto = relationship("Produto", back_populates="valores_campos_personalizados")
