from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LogAuditoriaOut(BaseModel):
    id: UUID
    usuario_id: UUID | None
    usuario_nome: str | None
    acao: str
    entidade: str
    entidade_id: UUID | None
    descricao: str
    criado_em: datetime

    model_config = {"from_attributes": True}


class MovimentacaoEstoqueOut(BaseModel):
    id: UUID
    produto_id: UUID
    produto_nome: str
    lote_id: UUID | None
    tipo: str
    quantidade: int
    estoque_resultante: int
    motivo: str | None
    usuario_nome: str | None
    criado_em: datetime
