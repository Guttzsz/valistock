from datetime import timedelta

from app.models.redefinicao_senha import RedefinicaoSenha
from app.utils.timezone import now
from tests.conftest import registrar_empresa

SENHA_NOVA = "OutraSenha456!"


def _capturar_emails(monkeypatch):
    enviados = []
    monkeypatch.setattr(
        "app.services.redefinicao_senha_service.enviar_email",
        lambda para, assunto, html, texto: enviados.append({"para": para, "texto": texto}) or True,
    )
    return enviados


def _token_do_email(enviado) -> str:
    return enviado["texto"].split("token=")[1].split()[0]


def _pedir(client, email="admina@example.com"):
    return client.post("/api/auth/esqueci-senha", json={"email": email})


def test_pedido_envia_link_para_conta_existente(client, monkeypatch):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    resp = _pedir(client)
    assert resp.status_code == 202
    assert len(enviados) == 1 and enviados[0]["para"] == "admina@example.com"
    assert "/templates/redefinir-senha.html?token=" in enviados[0]["texto"]


def test_pedido_para_email_desconhecido_responde_igual_e_nao_envia(client, monkeypatch):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    existente = _pedir(client)
    desconhecido = _pedir(client, "ninguem@example.com")
    assert desconhecido.status_code == existente.status_code == 202
    assert desconhecido.json() == existente.json()
    assert len(enviados) == 1


def test_redefinir_troca_a_senha_e_o_link_so_vale_uma_vez(client, monkeypatch):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    _pedir(client)
    token = _token_do_email(enviados[0])

    resp = client.post("/api/auth/redefinir-senha", json={"token": token, "senha_nova": SENHA_NOVA})
    assert resp.status_code == 204
    assert client.post("/api/auth/login", json={"email": "admina@example.com", "senha": SENHA_NOVA}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "admina@example.com", "senha": "SenhaForte123!"}).status_code == 401

    reuso = client.post("/api/auth/redefinir-senha", json={"token": token, "senha_nova": "MaisUma789!x"})
    assert reuso.status_code == 422


def test_novo_pedido_invalida_o_link_anterior(client, monkeypatch):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    _pedir(client)
    _pedir(client)
    antigo, novo = _token_do_email(enviados[0]), _token_do_email(enviados[1])

    assert client.post("/api/auth/redefinir-senha", json={"token": antigo, "senha_nova": SENHA_NOVA}).status_code == 422
    assert client.post("/api/auth/redefinir-senha", json={"token": novo, "senha_nova": SENHA_NOVA}).status_code == 204


def test_link_expirado_e_recusado(client, monkeypatch, db_session):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    _pedir(client)
    token = _token_do_email(enviados[0])

    for registro in db_session.query(RedefinicaoSenha).all():
        registro.expira_em = now() - timedelta(minutes=1)
    db_session.commit()

    assert client.post("/api/auth/redefinir-senha", json={"token": token, "senha_nova": SENHA_NOVA}).status_code == 422


def test_token_inventado_e_senha_fraca_sao_recusados(client, monkeypatch):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    _pedir(client)
    token = _token_do_email(enviados[0])

    assert client.post("/api/auth/redefinir-senha", json={"token": "x" * 43, "senha_nova": SENHA_NOVA}).status_code == 422
    assert client.post("/api/auth/redefinir-senha", json={"token": token, "senha_nova": "12345678"}).status_code == 422
    # a senha fraca nao gasta o link: com uma senha boa ele ainda funciona
    assert client.post("/api/auth/redefinir-senha", json={"token": token, "senha_nova": SENHA_NOVA}).status_code == 204


def test_token_fica_no_banco_so_como_hash(client, monkeypatch, db_session):
    registrar_empresa(client, "a")
    enviados = _capturar_emails(monkeypatch)
    _pedir(client)
    token = _token_do_email(enviados[0])
    assert all(r.token_hash != token and len(r.token_hash) == 64 for r in db_session.query(RedefinicaoSenha).all())
