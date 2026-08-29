import base64
import json
import secrets
from io import BytesIO

import pyotp
import qrcode

from app.auth.security import hash_password, verify_password

APP_NAME = "ValiStock"
QUANTIDADE_CODIGOS_BACKUP = 10


def gerar_segredo() -> str:
    return pyotp.random_base32()


def gerar_otpauth_url(segredo: str, email: str) -> str:
    return pyotp.TOTP(segredo).provisioning_uri(name=email, issuer_name=APP_NAME)


def gerar_qr_code_base64(otpauth_url: str) -> str:
    imagem = qrcode.make(otpauth_url)
    buffer = BytesIO()
    imagem.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def verificar_codigo_totp(segredo: str, codigo: str) -> bool:
    return pyotp.TOTP(segredo).verify(codigo, valid_window=1)


def gerar_codigos_backup() -> list[str]:
    return [secrets.token_hex(4).upper() for _ in range(QUANTIDADE_CODIGOS_BACKUP)]


def hash_codigos_backup(codigos: list[str]) -> str:
    return json.dumps([hash_password(codigo) for codigo in codigos])


def consumir_codigo_backup(hashes_json: str | None, codigo: str) -> str | None:
    """Se `codigo` bater com algum hash salvo, retorna o JSON atualizado sem aquele
    codigo (uso unico). Retorna None se nao encontrar (codigo invalido ou ja usado)."""
    if not hashes_json:
        return None

    hashes = json.loads(hashes_json)
    codigo_normalizado = codigo.strip().upper()
    for hash_atual in hashes:
        if verify_password(codigo_normalizado, hash_atual):
            hashes.remove(hash_atual)
            return json.dumps(hashes)
    return None
