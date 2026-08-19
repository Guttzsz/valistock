from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FornecedorCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    razao_social: str | None = None
    cnpj: str | None = None
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None
    observacao: str | None = None


class FornecedorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    razao_social: str | None = None
    cnpj: str | None = None
    telefone: str | None = None
    email: str | None = None
    endereco: str | None = None
    observacao: str | None = None
    ativo: bool | None = None


class FornecedorOut(BaseModel):
    id: UUID
    nome: str
    razao_social: str | None
    cnpj: str | None
    telefone: str | None
    email: str | None
    endereco: str | None
    observacao: str | None
    ativo: bool
    total_produtos: int = 0
    criado_em: datetime

    model_config = {"from_attributes": True}
