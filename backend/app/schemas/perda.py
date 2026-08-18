from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.perda import MotivoPerda


class PerdaCreate(BaseModel):
    produto_id: UUID
    lote_id: UUID | None = None
    quantidade: int = Field(gt=0)
    motivo: MotivoPerda
    observacao: str | None = None


class PerdaOut(BaseModel):
    id: UUID
    produto_id: UUID
    lote_id: UUID | None
    quantidade: int
    motivo: MotivoPerda
    valor_unitario: Decimal
    valor_total: Decimal
    data_perda: date
    observacao: str | None
    usuario_id: UUID | None
    criado_em: datetime

    model_config = {"from_attributes": True}


class PerdaComProduto(PerdaOut):
    produto_nome: str
    usuario_nome: str | None = None
