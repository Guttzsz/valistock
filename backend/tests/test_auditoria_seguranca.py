import pyotp

from tests.conftest import auth_headers, registrar_empresa

EMAIL = "admins@example.com"
SENHA = "SenhaForte123!"


def _acoes(client, headers):
    resp = client.get("/api/historico", headers=headers)
    assert resp.status_code == 200
    return [log["acao"] for log in resp.json()]


def test_login_correto_e_incorreto_geram_log(client):
    registrar_empresa(client, "s")
    headers = auth_headers(client.post("/api/auth/login", json={"email": EMAIL, "senha": SENHA}).json()["access_token"])

    client.post("/api/auth/login", json={"email": EMAIL, "senha": "senhaerrada"})

    acoes = _acoes(client, headers)
    assert acoes.count("usuario.login") == 1  # o cadastro nao gera log de login, so o login explicito acima
    assert "usuario.login_falhou" in acoes


def test_login_com_email_inexistente_nao_gera_log(client):
    data = registrar_empresa(client, "s2")
    headers = auth_headers(data["access_token"])

    client.post("/api/auth/login", json={"email": "ninguem@example.com", "senha": "x"})

    acoes = _acoes(client, headers)
    assert "usuario.login_falhou" not in acoes


def test_ativar_e_desativar_mfa_geram_log(client):
    data = registrar_empresa(client, "s3")
    headers = auth_headers(data["access_token"])

    segredo = client.post("/api/auth/mfa/setup", headers=headers).json()["secret"]
    client.post("/api/auth/mfa/enable", json={"codigo": pyotp.TOTP(segredo).now()}, headers=headers)
    client.post("/api/auth/mfa/disable", json={"senha": SENHA}, headers=headers)

    acoes = _acoes(client, headers)
    assert "usuario.mfa_ativado" in acoes
    assert "usuario.mfa_desativado" in acoes


def test_desativar_mfa_com_senha_errada_gera_log_de_falha(client):
    data = registrar_empresa(client, "s4")
    headers = auth_headers(data["access_token"])

    segredo = client.post("/api/auth/mfa/setup", headers=headers).json()["secret"]
    client.post("/api/auth/mfa/enable", json={"codigo": pyotp.TOTP(segredo).now()}, headers=headers)
    client.post("/api/auth/mfa/disable", json={"senha": "senhaerrada"}, headers=headers)

    assert "usuario.mfa_desativacao_falhou" in _acoes(client, headers)


def test_trocar_senha_gera_log_de_sucesso_e_falha(client):
    data = registrar_empresa(client, "s5")
    headers = auth_headers(data["access_token"])

    client.put("/api/auth/senha", json={"senha_atual": "senhaerrada", "senha_nova": "OutraSenha123"}, headers=headers)
    client.put("/api/auth/senha", json={"senha_atual": SENHA, "senha_nova": "OutraSenha123"}, headers=headers)

    acoes = _acoes(client, headers)
    assert "usuario.senha_alteracao_falhou" in acoes
    assert "usuario.senha_alterada" in acoes
