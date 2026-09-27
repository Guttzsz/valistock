from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.usuario import CorDestaque, TemaUsuario
from app.schemas.validators import validar_senha_forte


class RegisterRequest(BaseModel):
    empresa_nome_fantasia: str = Field(min_length=2, max_length=150)
    empresa_email: EmailStr
    admin_nome: str = Field(min_length=2, max_length=150)
    admin_email: EmailStr
    admin_senha: str = Field(min_length=8, max_length=100)

    _validar_senha = field_validator("admin_senha")(validar_senha_forte)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class AtualizarPerfilRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=150)


class TrocarSenhaRequest(BaseModel):
    senha_atual: str
    senha_nova: str = Field(min_length=8, max_length=100)

    _validar_senha = field_validator("senha_nova")(validar_senha_forte)


class AtualizarAparenciaRequest(BaseModel):
    theme: TemaUsuario
    accent_color: CorDestaque


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: "UsuarioMe"


class LoginResponse(BaseModel):
    """Resposta de /auth/login: ou o login ja termina aqui (mfa_required=False, com o
    access_token), ou o usuario tem MFA ativado e precisa trocar o challenge_token por um
    access_token real em /auth/mfa/verify."""

    mfa_required: bool = False
    challenge_token: str | None = None
    access_token: str | None = None
    token_type: str = "bearer"
    usuario: "UsuarioMe | None" = None


class MfaVerifyRequest(BaseModel):
    challenge_token: str
    codigo: str = Field(min_length=6, max_length=10)


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str


class MfaEnableRequest(BaseModel):
    codigo: str = Field(min_length=6, max_length=6)


class MfaEnableResponse(BaseModel):
    backup_codes: list[str]


class MfaDisableRequest(BaseModel):
    senha: str


class UsuarioMe(BaseModel):
    id: UUID
    empresa_id: UUID
    nome: str
    email: EmailStr
    perfil: str
    super_admin: bool = False
    theme: TemaUsuario
    accent_color: CorDestaque
    mfa_enabled: bool = False

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
LoginResponse.model_rebuild()
