from tests.conftest import auth_headers, registrar_empresa


def test_empresa_a_nao_ve_produtos_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")

    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    produto_a = client.post(
        "/api/produtos", json={"nome": "Produto da Empresa A", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers_a
    ).json()

    resp = client.get(f"/api/produtos/{produto_a['id']}", headers=headers_b)
    assert resp.status_code == 404

    lista_b = client.get("/api/produtos", headers=headers_b).json()
    assert lista_b == []


def test_empresa_a_nao_pode_editar_produto_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    produto_b = client.post(
        "/api/produtos", json={"nome": "Produto B", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers_b
    ).json()

    resp = client.put(f"/api/produtos/{produto_b['id']}", json={"nome": "Hackeado"}, headers=headers_a)
    assert resp.status_code == 404


def test_empresa_a_nao_ve_perdas_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    produto_b = client.post(
        "/api/produtos", json={"nome": "Produto B", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers_b
    ).json()
    client.post("/api/perdas", json={"produto_id": produto_b["id"], "quantidade": 1, "motivo": "outro"}, headers=headers_b)

    perdas_a = client.get("/api/perdas", headers=headers_a).json()
    assert perdas_a == []


def test_empresa_a_nao_ve_usuarios_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])

    usuarios_a = client.get("/api/usuarios", headers=headers_a).json()
    assert all(u["email"] != empresa_b["usuario"]["email"] for u in usuarios_a)


def test_dashboard_isolado_por_empresa(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    client.post("/api/produtos", json={"nome": "So da A", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers_a)

    dash_a = client.get("/api/dashboard", headers=headers_a).json()
    dash_b = client.get("/api/dashboard", headers=headers_b).json()
    assert dash_a["produtos_cadastrados"] == 1
    assert dash_b["produtos_cadastrados"] == 0
