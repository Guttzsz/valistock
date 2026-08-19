from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.auth.permissions import Permissao, tem_permissao
from app.database import get_db
from app.models.usuario import PerfilUsuario, Usuario
from app.utils.exceptions import PermissionDeniedError, UnauthorizedError

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """Authenticated principal. empresa_id is the sole source of tenant scoping."""

    def __init__(self, usuario: Usuario):
        self.id: UUID = usuario.id
        self.empresa_id: UUID = usuario.empresa_id
        self.perfil: PerfilUsuario = usuario.perfil
        self.nome: str = usuario.nome
        self.email: str = usuario.email
        self.super_admin: bool = usuario.super_admin


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise UnauthorizedError("Autenticacao necessaria.")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    usuario_id = payload.get("sub")
    usuario = db.get(Usuario, UUID(usuario_id)) if usuario_id else None

    if usuario is None or not usuario.ativo:
        raise UnauthorizedError("Usuario nao encontrado ou inativo.")

    return CurrentUser(usuario)


def require_perfil(*perfis: PerfilUsuario):
    """Dependency factory enforcing role-based authorization on a route."""

    def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.perfil not in perfis:
            raise PermissionDeniedError()
        return current_user

    return _check


require_admin = require_perfil(PerfilUsuario.ADMINISTRADOR)
require_gerente_ou_admin = require_perfil(PerfilUsuario.ADMINISTRADOR, PerfilUsuario.GERENTE)


def require_permissao(permissao: Permissao):
    """Dependency factory enforcing granular, backend-side authorization. Never trust the frontend for this."""

    def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not tem_permissao(current_user.perfil, permissao):
            raise PermissionDeniedError()
        return current_user

    return _check


def require_super_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Acesso cross-tenant (financeiro consolidado da plataforma ValiStock). Ortogonal ao perfil
    dentro de uma empresa: um administrador comum de uma empresa NUNCA passa aqui."""
    if not current_user.super_admin:
        raise PermissionDeniedError()
    return current_user
