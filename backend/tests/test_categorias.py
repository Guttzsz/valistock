from tests.conftest import auth_headers, registrar_empresa


def test_criar_categoria(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    resp = client.post("/api/categorias", json={"nome": "Laticinios"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Laticinios"
    assert resp.json()["total_produtos"] == 0


def test_categoria_duplicada_na_mesma_empresa_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    client.post("/api/categorias", json={"nome": "Laticinios"}, headers=headers)
    resp = client.post("/api/categorias", json={"nome": "Laticinios"}, headers=headers)
    assert resp.status_code == 409


def test_produto_com_categoria_conta_no_total(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    categoria = client.post("/api/categorias", json={"nome": "Laticinios"}, headers=headers).json()
    client.post(
        "/api/produtos",
        json={"nome": "Leite", "categoria_id": categoria["id"], "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1},
        headers=headers,
    )
    resp = client.get("/api/categorias", headers=headers)
    assert resp.json()[0]["total_produtos"] == 1


def test_desativar_categoria(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    categoria = client.post("/api/categorias", json={"nome": "Laticinios"}, headers=headers).json()

    resp = client.delete(f"/api/categorias/{categoria['id']}", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/api/categorias", headers=headers)
    assert resp.json() == []

    resp = client.get("/api/categorias", params={"incluir_inativas": True}, headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["ativo"] is False


def test_empresa_a_nao_ve_categorias_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    client.post("/api/categorias", json={"nome": "So da A"}, headers=headers_a)

    resp = client.get("/api/categorias", headers=headers_b)
    assert resp.json() == []


def test_empresa_a_nao_pode_editar_categoria_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    categoria_b = client.post("/api/categorias", json={"nome": "Categoria B"}, headers=headers_b).json()

    resp = client.put(f"/api/categorias/{categoria_b['id']}", json={"nome": "Hackeada"}, headers=headers_a)
    assert resp.status_code == 404


def test_produto_nao_pode_usar_categoria_de_outra_empresa(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    categoria_b = client.post("/api/categorias", json={"nome": "Categoria B"}, headers=headers_b).json()

    resp = client.post(
        "/api/produtos",
        json={"nome": "Produto A", "categoria_id": categoria_b["id"], "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1},
        headers=headers_a,
    )
    assert resp.status_code == 422


def test_funcionario_nao_pode_criar_categoria(client):
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    client.post(
        "/api/usuarios",
        json={"nome": "Func", "email": "func@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers_admin,
    )
    login = client.post("/api/auth/login", json={"email": "func@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.post("/api/categorias", json={"nome": "Nova"}, headers=headers_func)
    assert resp.status_code == 403
