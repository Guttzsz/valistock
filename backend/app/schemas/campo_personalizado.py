from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.campo_personalizado import TipoCampoPersonalizado


class CampoPersonalizadoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    tipo: TipoCampoPersonalizado
    obrigatorio: bool = False
    opcoes: list[str] | None = None  # usado apenas quando tipo == selecao


class CampoPersonalizadoUpdate(BaseModel):
    nome: str | None = None
    obrigatorio: bool | None = None
    opcoes: list[str] | None = None
    ativo: bool | None = None


class CampoPersonalizadoOut(BaseModel):
    id: UUID
    nome: str
    tipo: TipoCampoPersonalizado
    obrigatorio: bool
    opcoes: list[str] | None
    ativo: bool
    criado_em: datetime


class ValorCampoPersonalizadoIn(BaseModel):
    campo_id: UUID
    valor: str | None = None


class ValorCampoPersonalizadoOut(BaseModel):
    campo_id: UUID
    nome: str
    tipo: TipoCampoPersonalizado
    valor: str | None
