from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LocalizacaoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = None
    tipo: str | None = None


class LocalizacaoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    tipo: str | None = None
    ativo: bool | None = None


class LocalizacaoOut(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    tipo: str | None
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}
