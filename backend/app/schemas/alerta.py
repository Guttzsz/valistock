from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.alerta import TipoAlerta


class AlertaOut(BaseModel):
    id: UUID
    produto_id: UUID
    produto_nome: str
    lote_id: UUID | None
    tipo: TipoAlerta
    mensagem: str
    data_alerta: date
    lido: bool
    ignorado: bool
    criado_em: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_alerta(cls, alerta, produto_nome: str) -> "AlertaOut":
        return cls(
            id=alerta.id,
            produto_id=alerta.produto_id,
            produto_nome=produto_nome,
            lote_id=alerta.lote_id,
            tipo=alerta.tipo,
            mensagem=alerta.mensagem,
            data_alerta=alerta.data_alerta,
            lido=alerta.lido,
            ignorado=alerta.ignorado,
            criado_em=alerta.criado_em,
        )


class PromocaoCreate(BaseModel):
    desconto_percentual: int | None = None
    descricao: str | None = None
