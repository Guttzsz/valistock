import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    usuario_nome: Mapped[str | None] = mapped_column(String(150))  # snapshot: preserva o nome mesmo se o usuario for removido depois
    acao: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entidade: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
