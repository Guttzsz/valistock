from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
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
