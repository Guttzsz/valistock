from app.models.subscription import PlanoNome
from app.services.plano_service import LIMITES
from tests.conftest import auth_headers, registrar_empresa


def _payload_registro(senha: str) -> dict:
    return {
        "empresa_nome_fantasia": "Mercado Senha",
        "empresa_email": "mercado.senha@example.com",
        "admin_nome": "Admin Senha",
        "admin_email": "admin.senha@example.com",
        "admin_senha": senha,
    }


def test_cadastro_recusa_senha_so_numeros(client):
    resp = client.post("/api/auth/register", json=_payload_registro("12345678"))
    assert resp.status_code == 422


def test_cadastro_recusa_senha_comum(client):
    resp = client.post("/api/auth/register", json=_payload_registro("password1"))
    assert resp.status_code == 422


def test_cadastro_aceita_senha_com_letras_e_numeros(client):
    resp = client.post("/api/auth/register", json=_payload_registro("SenhaForte123"))
    assert resp.status_code == 201


def test_troca_de_senha_recusa_senha_fraca(client):
    data = registrar_empresa(client, "sf")
    headers = auth_headers(data["access_token"])
    resp = client.put(
        "/api/auth/senha",
        json={"senha_atual": "SenhaForte123!", "senha_nova": "12345678"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_criar_usuario_recusa_senha_fraca(client, monkeypatch):
    monkeypatch.setitem(LIMITES[PlanoNome.GRATUITO], "users", 5)
    data = registrar_empresa(client, "sf2")
    headers = auth_headers(data["access_token"])
    resp = client.post(
        "/api/usuarios",
        json={"nome": "Func", "email": "func.senha@example.com", "senha": "12345678", "perfil": "funcionario"},
        headers=headers,
    )
    assert resp.status_code == 422
