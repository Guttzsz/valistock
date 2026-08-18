from datetime import timedelta

from tests.conftest import auth_headers, registrar_empresa


def _criar_produto_e_lote(client, headers):
    produto = client.post(
        "/api/produtos",
        json={"nome": "Presunto", "preco_custo": "5.00", "preco_venda": "9.90", "estoque_minimo": 2},
        headers=headers,
    ).json()
    from app.utils.timezone import today

    lote = client.post(
        "/api/lotes",
        json={
            "produto_id": produto["id"],
            "numero_lote": "LT001",
            "quantidade": 10,
            "data_validade": str(today() + timedelta(days=5)),
            "custo_unitario": "5.00",
        },
        headers=headers,
    ).json()
    return produto, lote


def test_registrar_perda_calcula_valor_total(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto, lote = _criar_produto_e_lote(client, headers)

    resp = client.post(
        "/api/perdas",
        json={"produto_id": produto["id"], "lote_id": lote["id"], "quantidade": 8, "motivo": "produto_danificado"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["valor_unitario"] == "5.00"
    assert body["valor_total"] == "40.00"


def test_registrar_perda_reduz_estoque_do_produto(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto, lote = _criar_produto_e_lote(client, headers)

    client.post(
        "/api/perdas",
        json={"produto_id": produto["id"], "lote_id": lote["id"], "quantidade": 4, "motivo": "produto_vencido"},
        headers=headers,
    )

    produto_atualizado = client.get(f"/api/produtos/{produto['id']}", headers=headers).json()
    assert produto_atualizado["estoque_atual"] == 6


def test_registrar_perda_com_quantidade_maior_que_lote_falha(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto, lote = _criar_produto_e_lote(client, headers)

    resp = client.post(
        "/api/perdas",
        json={"produto_id": produto["id"], "lote_id": lote["id"], "quantidade": 999, "motivo": "outro"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_listar_perdas_filtra_por_periodo(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    produto, lote = _criar_produto_e_lote(client, headers)

    client.post(
        "/api/perdas",
        json={"produto_id": produto["id"], "lote_id": lote["id"], "quantidade": 2, "motivo": "outro"},
        headers=headers,
    )

    resp = client.get("/api/perdas", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["produto_nome"] == "Presunto"
