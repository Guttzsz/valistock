from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.lote import StatusLote


class LoteCreate(BaseModel):
    produto_id: UUID
    numero_lote: str = Field(min_length=1, max_length=50)
    quantidade: int = Field(gt=0)
    data_validade: date
    data_entrada: date | None = None
    custo_unitario: Decimal = Field(ge=0)


class LoteUpdate(BaseModel):
    numero_lote: str | None = None
    quantidade: int | None = Field(default=None, ge=0)
    data_validade: date | None = None
    custo_unitario: Decimal | None = Field(default=None, ge=0)
    status: StatusLote | None = None


class LoteOut(BaseModel):
    id: UUID
    produto_id: UUID
    numero_lote: str
    quantidade: int
    data_validade: date
    data_entrada: date
    custo_unitario: Decimal
    status: StatusLote
    criado_em: datetime

    model_config = {"from_attributes": True}


class ValidadeOut(BaseModel):
    lote_id: UUID
    produto_id: UUID
    produto_nome: str
    codigo_barras: str | None
    numero_lote: str
    quantidade: int
    data_validade: date
    dias_restantes: int
    valor_em_risco: Decimal
    status: str
