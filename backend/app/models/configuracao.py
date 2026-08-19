import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
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

    # Identidade / personalizacao da empresa
    tipo_estabelecimento: Mapped[str | None] = mapped_column(String(50))
    fuso_horario: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo", nullable=False)
    moeda: Mapped[str] = mapped_column(String(10), default="BRL", nullable=False)
    formato_data: Mapped[str] = mapped_column(String(20), default="DD/MM/AAAA", nullable=False)
    cor_principal: Mapped[str] = mapped_column(String(20), default="#16a34a", nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    horario_funcionamento: Mapped[str | None] = mapped_column(String(255))

    # Onboarding
    onboarding_concluido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_etapa: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quantidade_funcionarios_aprox: Mapped[str | None] = mapped_column(String(20))
    quantidade_produtos_aprox: Mapped[str | None] = mapped_column(String(20))

    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

    empresa = relationship("Empresa", back_populates="configuracao")
