import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.db_types import GUID
from app.utils.timezone import now


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    dias_alerta_1: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    dias_alerta_2: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    dias_alerta_3: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    empresa = relationship("Empresa", back_populates="configuracao")
