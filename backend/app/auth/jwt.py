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
