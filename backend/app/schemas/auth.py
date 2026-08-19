from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    empresa_nome_fantasia: str = Field(min_length=2, max_length=150)
    empresa_email: EmailStr
    admin_nome: str = Field(min_length=2, max_length=150)
    admin_email: EmailStr
    admin_senha: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class AtualizarPerfilRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=150)


class TrocarSenhaRequest(BaseModel):
    senha_atual: str
    senha_nova: str = Field(min_length=8, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: "UsuarioMe"


class UsuarioMe(BaseModel):
    id: UUID
    empresa_id: UUID
    nome: str
    email: EmailStr
    perfil: str

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
