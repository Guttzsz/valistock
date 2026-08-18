from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class EmpresaOut(BaseModel):
    id: UUID
    nome_fantasia: str
    razao_social: str | None
    cnpj: str | None
    email: EmailStr
    telefone: str | None
    endereco: str | None
    cidade: str | None
    estado: str | None
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class EmpresaUpdate(BaseModel):
    nome_fantasia: str | None = None
    razao_social: str | None = None
    cnpj: str | None = None
    telefone: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
