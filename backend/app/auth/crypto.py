from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

PREFIXO = "enc:v1:"

# Chave fixa e publica, usada SO fora de producao quando MFA_ENCRYPTION_KEY nao esta definida
# (desenvolvimento local). Em producao o main.py recusa subir sem a chave real.
_CHAVE_DEV = "ZGV2LW9ubHktbWZhLWtleS1ub3Qtc2VjcmV0LTEyMzQ="


def _fernet() -> Fernet:
    chave = get_settings().mfa_encryption_key or _CHAVE_DEV
    return Fernet(chave.encode())


def is_encrypted(valor: str) -> bool:
    return valor.startswith(PREFIXO)


def encrypt_secret(texto: str) -> str:
    return PREFIXO + _fernet().encrypt(texto.encode("utf-8")).decode("utf-8")


def decrypt_secret(valor: str) -> str:
    """Valores sem o prefixo sao segredos antigos, ainda em texto puro (anteriores a esta
    criptografia): devolvidos como estao e re-criptografados no proximo login bem-sucedido."""
    if not is_encrypted(valor):
        return valor
    try:
        return _fernet().decrypt(valor[len(PREFIXO):].encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Nao foi possivel descriptografar o segredo do MFA (chave incorreta?).") from exc
