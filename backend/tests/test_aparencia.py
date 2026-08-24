from tests.conftest import auth_headers, registrar_empresa


def test_novo_usuario_comeca_com_dia_e_verde(client):
    data = registrar_empresa(client, "a")
    assert data["usuario"]["theme"] == "dia"
    assert data["usuario"]["accent_color"] == "verde"


def test_atualizar_aparencia_persiste(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.put("/api/auth/aparencia", json={"theme": "noite", "accent_color": "roxo"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["theme"] == "noite"
    assert resp.json()["accent_color"] == "roxo"

    resp_me = client.get("/api/auth/me", headers=headers)
    assert resp_me.json()["theme"] == "noite"
    assert resp_me.json()["accent_color"] == "roxo"


def test_atualizar_aparencia_valor_invalido_rejeitado(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.put("/api/auth/aparencia", json={"theme": "roxo", "accent_color": "azul"}, headers=headers)
    assert resp.status_code == 422
