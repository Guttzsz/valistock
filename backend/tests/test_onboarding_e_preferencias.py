from tests.conftest import auth_headers, registrar_empresa


def test_onboarding_persiste_no_banco(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.put(
        "/api/configuracoes/onboarding",
        json={"etapa": 2, "tipo_estabelecimento": "padaria"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["tipo_estabelecimento"] == "padaria"
    assert resp.json()["onboarding_concluido"] is False

    resp = client.put(
        "/api/configuracoes/onboarding",
        json={"etapa": 9, "categorias_iniciais": ["Paes", "Doces"], "concluir": True},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["onboarding_concluido"] is True

    categorias = client.get("/api/categorias", headers=headers).json()
    nomes = {c["nome"] for c in categorias}
    assert nomes == {"Paes", "Doces"}

    # confirma persistencia real (nao apenas em memoria): busca de novo
    resp = client.get("/api/configuracoes", headers=headers)
    assert resp.json()["tipo_estabelecimento"] == "padaria"
    assert resp.json()["onboarding_concluido"] is True


def test_preferencias_notificacao_persistem(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.put("/api/preferencias/notificacoes", json={"produtos_vencendo": False, "relatorios": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["produtos_vencendo"] is False
    assert resp.json()["relatorios"] is True

    resp = client.get("/api/preferencias/notificacoes", headers=headers)
    assert resp.json()["produtos_vencendo"] is False


def test_preferencias_dashboard_persistem(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.put("/api/preferencias/dashboard", json={"widgets_ativos": ["produtos_cadastrados", "valor_em_risco"]}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["widgets_ativos"] == ["produtos_cadastrados", "valor_em_risco"]

    resp = client.get("/api/preferencias/dashboard", headers=headers)
    assert resp.json()["widgets_ativos"] == ["produtos_cadastrados", "valor_em_risco"]


def test_campo_personalizado_obrigatorio_bloqueia_valor_vazio(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    campo = client.post(
        "/api/campos-personalizados", json={"nome": "Prateleira", "tipo": "texto", "obrigatorio": True}, headers=headers
    ).json()
    produto = client.post(
        "/api/produtos", json={"nome": "Leite", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers
    ).json()

    resp = client.put(
        f"/api/produtos/{produto['id']}/campos-personalizados",
        json=[{"campo_id": campo["id"], "valor": ""}],
        headers=headers,
    )
    assert resp.status_code == 422

    resp = client.put(
        f"/api/produtos/{produto['id']}/campos-personalizados",
        json=[{"campo_id": campo["id"], "valor": "A3"}],
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()[0]["valor"] == "A3"


def test_permissoes_do_usuario_logado(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    resp = client.get("/api/auth/permissoes", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["perfil"] == "administrador"
    assert "empresa.gerenciar" in resp.json()["permissoes"]


def test_trocar_senha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.put("/api/auth/senha", json={"senha_atual": "SenhaForte123!", "senha_nova": "NovaSenha456!"}, headers=headers)
    assert resp.status_code == 204

    resp = client.post("/api/auth/login", json={"email": "admina@example.com", "senha": "NovaSenha456!"})
    assert resp.status_code == 200


def test_trocar_senha_com_senha_atual_errada_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    resp = client.put("/api/auth/senha", json={"senha_atual": "errada", "senha_nova": "NovaSenha456!"}, headers=headers)
    assert resp.status_code == 422
