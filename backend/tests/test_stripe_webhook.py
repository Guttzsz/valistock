import json
import time
from decimal import Decimal

from app.models.evento_stripe import EventoStripe
from app.models.fatura import Fatura, StatusFatura
from app.models.subscription import PlanoNome, StatusAssinatura, Subscription
from tests.conftest import assinar_webhook_stripe, auth_headers, registrar_empresa


def _post_webhook(client, event: dict):
    payload = json.dumps(event).encode()
    signature = assinar_webhook_stripe(payload)
    return client.post(
        "/api/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": signature, "Content-Type": "application/json"},
    )


def _evento_subscription(evento_id, tipo, empresa_id, status="active", price_id="price_test_basico", unit_amount=4990):
    ts = int(time.time())
    return {
        "id": evento_id,
        "type": tipo,
        "data": {
            "object": {
                "id": "sub_test_123",
                "customer": "cus_test_123",
                "status": status,
                "cancel_at_period_end": False,
                "current_period_end": ts + 30 * 86400,
                "start_date": ts,
                "trial_end": None,
                "metadata": {"empresa_id": empresa_id},
                "items": {
                    "data": [
                        {
                            "current_period_end": ts + 30 * 86400,
                            "price": {"id": price_id, "unit_amount": unit_amount, "currency": "brl"},
                        }
                    ]
                },
            }
        },
    }


def _evento_invoice(evento_id, tipo, empresa_id, status="paid", amount_paid=4990, amount_due=4990):
    ts = int(time.time())
    return {
        "id": evento_id,
        "type": tipo,
        "data": {
            "object": {
                "id": f"in_{evento_id}",
                "customer": "cus_test_123",
                "status": status,
                "amount_due": amount_due,
                "amount_paid": amount_paid,
                "amount_remaining": amount_due - amount_paid,
                "currency": "brl",
                "number": "INV-0001",
                "hosted_invoice_url": "https://invoice.stripe.com/test",
                "invoice_pdf": "https://invoice.stripe.com/test.pdf",
                "status_transitions": {"paid_at": ts},
                "lines": {"data": [{"period": {"start": ts, "end": ts + 30 * 86400}}]},
                "subscription_details": {"metadata": {"empresa_id": empresa_id}},
            }
        },
    }


def test_webhook_rejeita_assinatura_invalida(client):
    payload = json.dumps({"id": "evt_1", "type": "customer.subscription.created", "data": {"object": {}}}).encode()
    resp = client.post(
        "/api/stripe/webhook",
        content=payload,
        headers={"Stripe-Signature": "t=123,v1=assinatura_forjada", "Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_webhook_subscription_created_sincroniza_assinatura(client, db_session):
    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]

    resp = _post_webhook(client, _evento_subscription("evt_sub_created", "customer.subscription.created", empresa_id))
    assert resp.status_code == 200

    sub = db_session.query(Subscription).filter(Subscription.empresa_id == empresa_id).first()
    assert sub.status == StatusAssinatura.ACTIVE
    assert sub.plano == PlanoNome.BASICO
    assert sub.valor_mensal == Decimal("49.90")
    assert sub.stripe_customer_id == "cus_test_123"


def test_webhook_subscription_deleted_marca_cancelada(client, db_session):
    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]

    _post_webhook(client, _evento_subscription("evt_sub_created_2", "customer.subscription.created", empresa_id))
    resp = _post_webhook(client, _evento_subscription("evt_sub_deleted", "customer.subscription.deleted", empresa_id, status="canceled"))
    assert resp.status_code == 200

    sub = db_session.query(Subscription).filter(Subscription.empresa_id == empresa_id).first()
    assert sub.status == StatusAssinatura.CANCELED
    assert sub.data_fim is not None


def test_webhook_invoice_paid_cria_fatura(client, db_session):
    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]
    _post_webhook(client, _evento_subscription("evt_sub_created_3", "customer.subscription.created", empresa_id))

    resp = _post_webhook(client, _evento_invoice("evt_invoice_paid", "invoice.paid", empresa_id))
    assert resp.status_code == 200

    fatura = db_session.query(Fatura).filter(Fatura.empresa_id == empresa_id).first()
    assert fatura is not None
    assert fatura.status == StatusFatura.PAGA
    assert fatura.valor_pago == Decimal("49.90")


def test_webhook_invoice_payment_failed_marca_pendente(client, db_session):
    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]
    _post_webhook(client, _evento_subscription("evt_sub_created_4", "customer.subscription.created", empresa_id))

    resp = _post_webhook(
        client, _evento_invoice("evt_invoice_failed", "invoice.payment_failed", empresa_id, status="open", amount_paid=0)
    )
    assert resp.status_code == 200

    fatura = db_session.query(Fatura).filter(Fatura.empresa_id == empresa_id).first()
    assert fatura.status == StatusFatura.PENDENTE


def test_webhook_e_idempotente(client, db_session):
    data = registrar_empresa(client, "a")
    empresa_id = data["usuario"]["empresa_id"]

    evento = _evento_subscription("evt_idempotente", "customer.subscription.created", empresa_id)
    resp1 = _post_webhook(client, evento)
    assert resp1.status_code == 200

    # Reenvia o mesmo evento (Stripe faz isso quando nao recebe 2xx a tempo, ou por seguranca).
    resp2 = _post_webhook(client, evento)
    assert resp2.status_code == 200

    total_eventos = db_session.query(EventoStripe).filter(EventoStripe.stripe_event_id == "evt_idempotente").count()
    assert total_eventos == 1

    total_subscriptions = db_session.query(Subscription).filter(Subscription.empresa_id == empresa_id).count()
    assert total_subscriptions == 1
