from datetime import timedelta

from tests.conftest import auth_headers, registrar_empresa


def test_criar_produto_gera_log_de_auditoria(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    client.post("/api/produtos", json={"nome": "Leite", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers)

    resp = client.get("/api/historico", headers=headers)
    assert resp.status_code == 200
    acoes = [log["acao"] for log in resp.json()]
    assert "produto.criado" in acoes


def test_criar_lote_gera_movimentacao_de_estoque(client):
    from app.utils.timezone import today

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = client.post(
        "/api/produtos", json={"nome": "Leite", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers
    ).json()
    client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"], "numero_lote": "LT001", "quantidade": 20,
            "data_validade": str(today() + timedelta(days=30)), "custo_unitario": "1.00",
        },
        headers=headers,
    )

    resp = client.get("/api/historico/estoque", headers=headers)
    assert resp.status_code == 200
    movimentos = resp.json()
    assert len(movimentos) == 1
    assert movimentos[0]["tipo"] == "entrada"
    assert movimentos[0]["quantidade"] == 20
    assert movimentos[0]["estoque_resultante"] == 20


def test_registrar_perda_gera_movimentacao_de_estoque(client):
    from app.utils.timezone import today

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = client.post(
        "/api/produtos", json={"nome": "Leite", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers
    ).json()
    lote = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"], "numero_lote": "LT001", "quantidade": 20,
            "data_validade": str(today() + timedelta(days=30)), "custo_unitario": "1.00",
        },
        headers=headers,
    ).json()
    client.post(
        "/api/perdas",
        json={"produto_id": produto["id"], "lote_id": lote["id"], "quantidade": 5, "motivo": "outro"},
        headers=headers,
    )

    resp = client.get("/api/historico/estoque", params={"produto_id": produto["id"]}, headers=headers)
    tipos = [m["tipo"] for m in resp.json()]
    assert "perda" in tipos


def test_empresa_a_nao_ve_historico_da_empresa_b(client):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    headers_b = auth_headers(empresa_b["access_token"])

    client.post("/api/produtos", json={"nome": "Produto B", "preco_custo": "1", "preco_venda": "2", "estoque_minimo": 1}, headers=headers_b)

    resp = client.get("/api/historico", headers=headers_a)
    assert resp.json() == []


def test_funcionario_nao_pode_ver_historico(client):
    data = registrar_empresa(client, "a")
    headers_admin = auth_headers(data["access_token"])
    client.post(
        "/api/usuarios",
        json={"nome": "Func", "email": "func@example.com", "senha": "SenhaForte123!", "perfil": "funcionario"},
        headers=headers_admin,
    )
    login = client.post("/api/auth/login", json={"email": "func@example.com", "senha": "SenhaForte123!"}).json()
    headers_func = auth_headers(login["access_token"])

    resp = client.get("/api/historico", headers=headers_func)
    assert resp.status_code == 403
