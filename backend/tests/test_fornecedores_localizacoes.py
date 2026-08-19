from tests.conftest import auth_headers, registrar_empresa


def test_criar_fornecedor(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    resp = client.post("/api/fornecedores", json={"nome": "Distribuidora Central", "cnpj": "12345678000100"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Distribuidora Central"


def test_empresa_a_nao_ve_fornecedores_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    client.post("/api/fornecedores", json={"nome": "Fornecedor B"}, headers=headers_b)

    resp = client.get("/api/fornecedores", headers=headers_a)
    assert resp.json() == []


def test_desativar_fornecedor(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    fornecedor = client.post("/api/fornecedores", json={"nome": "Fornecedor"}, headers=headers).json()

    resp = client.delete(f"/api/fornecedores/{fornecedor['id']}", headers=headers)
    assert resp.status_code == 204
    assert client.get("/api/fornecedores", headers=headers).json() == []


def test_criar_localizacao(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    resp = client.post("/api/localizacoes", json={"nome": "Geladeira 2", "tipo": "geladeira"}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Geladeira 2"


def test_empresa_a_nao_ve_localizacoes_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    client.post("/api/localizacoes", json={"nome": "Local B"}, headers=headers_b)

    resp = client.get("/api/localizacoes", headers=headers_a)
    assert resp.json() == []


def test_produto_com_fornecedor_e_localizacao(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    fornecedor = client.post("/api/fornecedores", json={"nome": "Fornecedor"}, headers=headers).json()
    localizacao = client.post("/api/localizacoes", json={"nome": "Geladeira 1"}, headers=headers).json()

    resp = client.post(
        "/api/produtos",
        json={
            "nome": "Leite",
            "fornecedor_id": fornecedor["id"],
            "localizacao_id": localizacao["id"],
            "preco_custo": "1",
            "preco_venda": "2",
            "estoque_minimo": 1,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["fornecedor_nome"] == "Fornecedor"
    assert resp.json()["localizacao_nome"] == "Geladeira 1"
