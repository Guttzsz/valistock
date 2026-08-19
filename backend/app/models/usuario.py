import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class PerfilUsuario(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    GERENTE = "gerente"
    FUNCIONARIO = "funcionario"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(100))
    perfil: Mapped[PerfilUsuario] = mapped_column(Enum(PerfilUsuario, name="perfil_usuario", values_callable=lambda enum_cls: [e.value for e in enum_cls]), default=PerfilUsuario.FUNCIONARIO, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    empresa = relationship("Empresa", back_populates="usuarios")
