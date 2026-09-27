from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.usuario import PerfilUsuario
from app.schemas.validators import validar_senha_forte


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=100)
    cargo: str | None = None
    perfil: PerfilUsuario = PerfilUsuario.FUNCIONARIO

    _validar_senha = field_validator("senha")(validar_senha_forte)


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    cargo: str | None = None
    perfil: PerfilUsuario | None = None
    ativo: bool | None = None


class UsuarioOut(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    cargo: str | None
    perfil: PerfilUsuario
    ativo: bool
    criado_em: datetime
    ultimo_login: datetime | None

    model_config = {"from_attributes": True}
