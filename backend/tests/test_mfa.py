import pyotp
import pytest

from app.auth.crypto import PREFIXO, decrypt_secret, encrypt_secret
from app.models.usuario import Usuario
from tests.conftest import auth_headers, registrar_empresa

EMAIL = "adminm@example.com"
SENHA = "SenhaForte123!"


def _usuario_no_banco(db_session) -> Usuario:
    usuario = db_session.query(Usuario).filter(Usuario.email == EMAIL).first()
    db_session.refresh(usuario)
    return usuario


def _ativar_mfa(client, sufixo="m"):
    data = registrar_empresa(client, sufixo)
    headers = auth_headers(data["access_token"])
    segredo = client.post("/api/auth/mfa/setup", headers=headers).json()["secret"]
    resp = client.post("/api/auth/mfa/enable", json={"codigo": pyotp.TOTP(segredo).now()}, headers=headers)
    assert resp.status_code == 200
    return segredo, resp.json()["backup_codes"]


def _login_com_desafio(client) -> str:
    resp = client.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA})
    assert resp.status_code == 200
    assert resp.json()["mfa_required"] is True
    return resp.json()["challenge_token"]


def test_segredo_mfa_e_salvo_criptografado_no_banco(client, db_session):
    data = registrar_empresa(client, "m")
    headers = auth_headers(data["access_token"])

    segredo = client.post("/api/auth/mfa/setup", headers=headers).json()["secret"]

    salvo = _usuario_no_banco(db_session).mfa_secret
    assert salvo.startswith(PREFIXO)
    assert segredo not in salvo
    assert decrypt_secret(salvo) == segredo


def test_login_com_mfa_aceita_totp_e_codigo_de_backup_uma_unica_vez(client):
    segredo, codigos_backup = _ativar_mfa(client)

    challenge = _login_com_desafio(client)
    resp = client.post("/api/auth/mfa/verify", json={"challenge_token": challenge, "codigo": pyotp.TOTP(segredo).now()})
    assert resp.status_code == 200
    assert resp.json()["access_token"]

    challenge = _login_com_desafio(client)
    resp = client.post("/api/auth/mfa/verify", json={"challenge_token": challenge, "codigo": codigos_backup[0]})
    assert resp.status_code == 200

    challenge = _login_com_desafio(client)
    resp = client.post("/api/auth/mfa/verify", json={"challenge_token": challenge, "codigo": codigos_backup[0]})
    assert resp.status_code == 401


def test_codigo_totp_errado_e_recusado(client):
    _ativar_mfa(client)
    challenge = _login_com_desafio(client)
    resp = client.post("/api/auth/mfa/verify", json={"challenge_token": challenge, "codigo": "000000"})
    assert resp.status_code == 401


def test_segredo_antigo_em_texto_puro_continua_valendo_e_e_recriptografado(client, db_session):
    segredo, _ = _ativar_mfa(client)

    usuario = _usuario_no_banco(db_session)
    usuario.mfa_secret = segredo
    db_session.commit()

    challenge = _login_com_desafio(client)
    resp = client.post("/api/auth/mfa/verify", json={"challenge_token": challenge, "codigo": pyotp.TOTP(segredo).now()})
    assert resp.status_code == 200

    salvo = _usuario_no_banco(db_session).mfa_secret
    assert salvo.startswith(PREFIXO)
    assert decrypt_secret(salvo) == segredo


def test_desativar_mfa_apaga_o_segredo(client, db_session):
    _ativar_mfa(client)
    challenge = _login_com_desafio(client)
    segredo = decrypt_secret(_usuario_no_banco(db_session).mfa_secret)
    token = client.post(
        "/api/auth/mfa/verify", json={"challenge_token": challenge, "codigo": pyotp.TOTP(segredo).now()}
    ).json()["access_token"]

    resp = client.post("/api/auth/mfa/disable", json={"senha": SENHA}, headers=auth_headers(token))
    assert resp.status_code == 204
    usuario = _usuario_no_banco(db_session)
    assert usuario.mfa_enabled is False
    assert usuario.mfa_secret is None


def test_cripto_ida_e_volta_e_cada_cifra_e_diferente():
    a = encrypt_secret("ABCDEFGHIJKLMNOP")
    b = encrypt_secret("ABCDEFGHIJKLMNOP")
    assert a != b
    assert decrypt_secret(a) == decrypt_secret(b) == "ABCDEFGHIJKLMNOP"


def test_valor_adulterado_nao_descriptografa():
    adulterado = encrypt_secret("ABCDEFGHIJKLMNOP")[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt_secret(adulterado)
