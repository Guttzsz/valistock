from decimal import Decimal

from app.models.subscription import PlanoNome, StatusAssinatura, Subscription
from tests.conftest import auth_headers, registrar_empresa, tornar_super_admin


def test_admin_comum_nao_acessa_financeiro(client):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])

    resp = client.get("/api/financeiro/dashboard", headers=headers)
    assert resp.status_code == 403


def test_super_admin_acessa_financeiro(client, db_session):
    data = registrar_empresa(client, "a")
    headers = auth_headers(data["access_token"])
    tornar_super_admin(db_session, "admina@example.com")

    resp = client.get("/api/financeiro/dashboard", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "mrr" in body
    assert "assinaturas_ativas" in body


def test_financeiro_agrega_todas_as_empresas(client, db_session):
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])
    tornar_super_admin(db_session, "admina@example.com")

    sub_a = Subscription(
        empresa_id=empresa_a["usuario"]["empresa_id"],
        plano=PlanoNome.ESSENCIAL,
        status=StatusAssinatura.ACTIVE,
        valor_mensal=Decimal("49.90"),
        stripe_customer_id="cus_a",
    )
    sub_b = Subscription(
        empresa_id=empresa_b["usuario"]["empresa_id"],
        plano=PlanoNome.PROFISSIONAL,
        status=StatusAssinatura.ACTIVE,
        valor_mensal=Decimal("99.90"),
        stripe_customer_id="cus_b",
    )
    db_session.add_all([sub_a, sub_b])
    db_session.commit()

    resp = client.get("/api/financeiro/dashboard", headers=headers_a)
    body = resp.json()
    assert Decimal(body["mrr"]) == Decimal("149.80")
    assert body["clientes_pagantes"] == 2

    resp_assinaturas = client.get("/api/financeiro/assinaturas", headers=headers_a)
    nomes = {a["empresa_nome"] for a in resp_assinaturas.json()}
    assert nomes == {"Mercado a", "Mercado b"}


def test_cliente_nao_ve_financeiro_de_outras_empresas_na_propria_assinatura(client, db_session):
    """O endpoint /api/subscriptions/atual (visao do cliente) nunca deve vazar dados de outra empresa."""
    empresa_a = registrar_empresa(client, "a")
    empresa_b = registrar_empresa(client, "b")
    headers_a = auth_headers(empresa_a["access_token"])

    sub_b = Subscription(
        empresa_id=empresa_b["usuario"]["empresa_id"],
        plano=PlanoNome.PROFISSIONAL,
        status=StatusAssinatura.ACTIVE,
        valor_mensal=Decimal("99.90"),
    )
    db_session.add(sub_b)
    db_session.commit()

    resp = client.get("/api/subscriptions/atual", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json()["plano"] == "gratuito"


def test_receita_por_plano_soma_corretamente(client, db_session):
    empresa_a = registrar_empresa(client, "a")
    headers_a = auth_headers(empresa_a["access_token"])
    tornar_super_admin(db_session, "admina@example.com")

    db_session.add(
        Subscription(
            empresa_id=empresa_a["usuario"]["empresa_id"],
            plano=PlanoNome.ESSENCIAL,
            status=StatusAssinatura.ACTIVE,
            valor_mensal=Decimal("49.90"),
        )
    )
    db_session.commit()

    resp = client.get("/api/financeiro/receita-por-plano", headers=headers_a)
    assert resp.status_code == 200
    essencial = next(p for p in resp.json() if p["plano"] == "essencial")
    assert Decimal(essencial["receita_mensal"]) == Decimal("49.90")
    assert Decimal(essencial["percentual"]) == Decimal("100.0")
