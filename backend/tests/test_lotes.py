from datetime import timedelta

from tests.conftest import auth_headers, registrar_empresa


def _criar_produto(client, headers):
    resp = client.post(
        "/api/produtos",
        json={"nome": "Iogurte", "preco_custo": "2.00", "preco_venda": "3.50", "estoque_minimo": 5},
        headers=headers,
    )
    return resp.json()


def test_criar_lote_atualiza_estoque_do_produto(client):
    from app.utils.timezone import today

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = _criar_produto(client, headers)

    resp = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"],
            "numero_lote": "LT001",
            "quantidade": 20,
            "data_validade": str(today() + timedelta(days=30)),
            "custo_unitario": "2.00",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "ativo"

    produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=headers).json()
    assert produto_atualizado["estoque_atual"] == 20


def test_lote_com_validade_passada_marca_status_vencido(client):
    from app.utils.timezone import today

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = _criar_produto(client, headers)

    resp = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"],
            "numero_lote": "LT002",
            "quantidade": 5,
            "data_validade": str(today() - timedelta(days=3)),
            "custo_unitario": "2.00",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "vencido"


def test_remover_lote_devolve_estoque(client):
    from app.utils.timezone import today

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = _criar_produto(client, headers)

    lote = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"],
            "numero_lote": "LT003",
            "quantidade": 10,
            "data_validade": str(today() + timedelta(days=10)),
            "custo_unitario": "2.00",
        },
        headers=headers,
    ).json()

    resp = client.delete(f"/api/lotes/{lote['id']}", headers=headers)
    assert resp.status_code == 204

    produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=headers).json()
    assert produto_atualizado["estoque_atual"] == 0


def test_marcar_lote_como_vendido(client):
    from app.utils.timezone import today

    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto = _criar_produto(client, headers)

    lote = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"],
            "numero_lote": "LT004",
            "quantidade": 8,
            "data_validade": str(today() + timedelta(days=2)),
            "custo_unitario": "2.00",
        },
        headers=headers,
    ).json()

    resp = client.put(f"/api/lotes/{lote['id']}/marcar-vendido", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "esgotado"
    assert resp.json()["quantidade"] == 0

    produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=headers).json()
    assert produto_atualizado["estoque_atual"] == 0
