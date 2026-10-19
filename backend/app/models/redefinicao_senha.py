import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class RedefinicaoSenha(Base):
    """Token de uso unico para redefinir a senha. So o hash (SHA-256) fica no banco: quem ler a
    tabela nao consegue montar o link que chegou por e-mail."""

    __tablename__ = "redefinicoes_senha"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
