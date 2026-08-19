import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    razao_social: Mapped[str | None] = mapped_column(String(150))
    cnpj: Mapped[str | None] = mapped_column(String(20))
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150))
    endereco: Mapped[str | None] = mapped_column(String(255))
    observacao: Mapped[str | None] = mapped_column(String(500))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    produtos = relationship("Produto", back_populates="fornecedor")
