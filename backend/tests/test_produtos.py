from tests.conftest import auth_headers, registrar_empresa


def _criar_produto(client, headers, **overrides):
    payload = {
        "codigo_barras": "7891000100103",
        "nome": "Leite Integral 1L",
        "categoria": "Laticinios",
        "unidade_medida": "UN",
        "preco_custo": "4.20",
        "preco_venda": "6.50",
        "estoque_minimo": 10,
    }
    payload.update(overrides)
    return client.post("/api/produtos", json=payload, headers=headers)


def test_criar_produto(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    resp = _criar_produto(client, headers)
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Leite Integral 1L"


def test_codigo_barras_duplicado_na_mesma_empresa_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    _criar_produto(client, headers)
    resp = _criar_produto(client, headers, nome="Outro Produto")
    assert resp.status_code == 409


def test_listar_produtos_com_busca(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    _criar_produto(client, headers)
    _criar_produto(client, headers, codigo_barras="000", nome="Queijo Mussarela")

    resp = client.get("/api/produtos", params={"q": "leite"}, headers=headers)
    assert resp.status_code == 200
    nomes = [p["nome"] for p in resp.json()]
    assert nomes == ["Leite Integral 1L"]


def test_atualizar_produto(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = _criar_produto(client, headers).json()

    resp = client.put(f"/api/produtos/{produto['id']}", json={"preco_venda": "7.00"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["preco_venda"] == "7.00"


def test_remover_produto(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = _criar_produto(client, headers).json()

    resp = client.delete(f"/api/produtos/{produto['id']}", headers=headers)
    assert resp.status_code == 204

    resp = client.get(f"/api/produtos/{produto['id']}", headers=headers)
    assert resp.status_code == 404
