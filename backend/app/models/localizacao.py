import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class Localizacao(Base):
    __tablename__ = "localizacoes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255))
    tipo: Mapped[str | None] = mapped_column(String(50))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    produtos = relationship("Produto", back_populates="localizacao")
