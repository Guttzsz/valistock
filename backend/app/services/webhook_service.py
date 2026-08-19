import logging

from sqlalchemy.orm import Session

from app.services.stripe_service import (
    evento_ja_processado,
    marcar_evento_processado,
    registrar_evento,
    registrar_reembolso,
    sincronizar_fatura,
    sincronizar_subscription,
)

logger = logging.getLogger("valistock")

EVENTOS_TRATADOS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
    "charge.refunded",
}


def processar_evento(db: Session, event: dict) -> None:
    """Ponto unico de entrada para eventos de webhook do Stripe. Idempotente: reprocessar o mesmo
    stripe_event_id nao duplica nada (checado antes de qualquer efeito colateral)."""
    stripe_event_id = event["id"]
    tipo = event["type"]

    if evento_ja_processado(db, stripe_event_id):
        logger.info("Evento Stripe %s (%s) ja processado, ignorando.", stripe_event_id, tipo)
        return

    evento_registro = registrar_evento(db, stripe_event_id, tipo)

    try:
        # O SDK do Stripe retorna StripeObject (so suporta obj["chave"], nao .get()) - convertendo
        # para dict puro recursivamente aqui deixa o resto do codigo simples e testavel com dicts comuns.
        obj = event["data"]["object"].to_dict()

        if tipo in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
            sincronizar_subscription(db, obj)
        elif tipo in ("invoice.paid", "invoice.payment_failed"):
            sincronizar_fatura(db, obj)
        elif tipo == "charge.refunded":
            for refund in (obj.get("refunds") or {}).get("data", []):
                registrar_reembolso(db, refund)
        elif tipo == "checkout.session.completed":
            # A subscription criada pelo checkout dispara customer.subscription.created em seguida,
            # que e quem efetivamente sincroniza o plano/status. Nada adicional a fazer aqui.
            pass
        else:
            logger.info("Evento Stripe %s recebido mas sem handler especifico.", tipo)

        marcar_evento_processado(db, evento_registro)
    except Exception as exc:
        logger.exception("Erro ao processar evento Stripe %s (%s)", stripe_event_id, tipo)
        marcar_evento_processado(db, evento_registro, erro=str(exc)[:900])
        raise
