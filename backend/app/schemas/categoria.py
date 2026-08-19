from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    descricao: str | None = None


class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    descricao: str | None = None
    ativo: bool | None = None


class CategoriaOut(BaseModel):
    id: UUID
    nome: str
    descricao: str | None
    ativo: bool
    total_produtos: int = 0
    criado_em: datetime

    model_config = {"from_attributes": True}
