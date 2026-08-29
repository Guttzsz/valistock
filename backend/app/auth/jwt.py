from datetime import timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.config import get_settings
from app.utils.timezone import now

settings = get_settings()
ALGORITHM = "HS256"


def create_access_token(usuario_id: UUID, empresa_id: UUID, perfil: str) -> str:
    expire = now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(usuario_id),
        "empresa_id": str(empresa_id),
        "perfil": perfil,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token invalido ou expirado.") from exc


def create_mfa_challenge_token(usuario_id: UUID) -> str:
    """Token de curta duracao emitido apos validar email+senha quando o usuario tem MFA
    ativado. So serve para trocar por um access_token real em /mfa/verify."""
    expire = now() + timedelta(minutes=5)
    payload = {"sub": str(usuario_id), "mfa_challenge": True, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_mfa_challenge_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Sessao de verificacao invalida ou expirada. Faca login novamente.") from exc

    if not payload.get("mfa_challenge"):
        raise ValueError("Token invalido.")
    return UUID(payload["sub"])
