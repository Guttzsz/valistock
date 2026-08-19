from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.fatura import StatusFatura
from app.models.subscription import PlanoNome, StatusAssinatura


class SubscriptionOut(BaseModel):
    plano: PlanoNome
    status: StatusAssinatura
    limite_produtos: int | None
    limite_usuarios: int | None
    valor_mensal: Decimal = Decimal(0)
    periodo_atual_fim: date | None = None
    trial_fim: date | None = None
    cancelar_ao_fim_periodo: bool = False
    possui_stripe: bool = False


class CheckoutRequest(BaseModel):
    plano: str  # "basico" ou "profissional"


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class FaturaOut(BaseModel):
    id: UUID
    numero: str | None
    valor_total: Decimal
    valor_pago: Decimal
    moeda: str
    status: StatusFatura
    periodo_inicio: date | None
    periodo_fim: date | None
    url_fatura: str | None
    url_pdf: str | None
    pago_em: datetime | None
    criado_em: datetime

    model_config = {"from_attributes": True}
