import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.empresa import Empresa
from app.models.evento_stripe import EventoStripe
from app.models.fatura import Fatura, StatusFatura
from app.models.reembolso import Reembolso
from app.models.subscription import PlanoNome, StatusAssinatura, Subscription
from app.utils.exceptions import ValidationErrorApp

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

STRIPE_STATUS_MAP = {
    "trialing": StatusAssinatura.TRIALING,
    "active": StatusAssinatura.ACTIVE,
    "past_due": StatusAssinatura.PAST_DUE,
    "canceled": StatusAssinatura.CANCELED,
    "unpaid": StatusAssinatura.UNPAID,
    "incomplete": StatusAssinatura.INCOMPLETE,
    "incomplete_expired": StatusAssinatura.CANCELED,
}


def _price_para_plano(price_id: str | None) -> PlanoNome | None:
    if price_id and price_id == settings.stripe_price_basic:
        return PlanoNome.BASICO
    if price_id and price_id == settings.stripe_price_pro:
        return PlanoNome.PROFISSIONAL
    return None


def _timestamp_para_date(ts: int | None) -> date | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).date()


def _timestamp_para_datetime(ts: int | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _current_period_end(stripe_sub: dict) -> int | None:
    """current_period_end pode estar no nivel da subscription ou, em versoes mais novas da API do Stripe, no item."""
    if stripe_sub.get("current_period_end"):
        return stripe_sub["current_period_end"]
    itens = (stripe_sub.get("items") or {}).get("data") or []
    if itens:
        return itens[0].get("current_period_end")
    return None


def _get_or_create_local_subscription(db: Session, empresa_id: uuid.UUID) -> Subscription:
    sub = db.scalar(select(Subscription).where(Subscription.empresa_id == empresa_id))
    if sub is None:
        sub = Subscription(empresa_id=empresa_id)
        db.add(sub)
        db.flush()
    return sub


def obter_ou_criar_customer(db: Session, empresa: Empresa) -> str:
    """Garante um unico Stripe Customer por empresa (nunca cria duplicado)."""
    sub = _get_or_create_local_subscription(db, empresa.id)
    if sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=empresa.email,
        name=empresa.nome_fantasia,
        metadata={"empresa_id": str(empresa.id)},
    )
    sub.stripe_customer_id = customer.id
    db.commit()
    return customer.id


def criar_checkout_session(db: Session, empresa: Empresa, price_id: str) -> str:
    if price_id not in (settings.stripe_price_basic, settings.stripe_price_pro):
        raise ValidationErrorApp("Plano invalido.")

    customer_id = obter_ou_criar_customer(db, empresa)
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.stripe_success_url,
        cancel_url=settings.stripe_cancel_url,
        client_reference_id=str(empresa.id),
        subscription_data={"metadata": {"empresa_id": str(empresa.id)}},
    )
    return session.url


def criar_portal_session(db: Session, empresa: Empresa) -> str:
    sub = _get_or_create_local_subscription(db, empresa.id)
    if not sub.stripe_customer_id:
        raise ValidationErrorApp("Esta empresa ainda nao possui uma assinatura no Stripe.")

    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{settings.frontend_url}/templates/planos.html",
    )
    return portal.url


def sincronizar_subscription(db: Session, stripe_sub: dict) -> Subscription | None:
    """Atualiza a copia local a partir de um objeto Subscription do Stripe (evento de webhook ou GET direto)."""
    empresa_id_str = (stripe_sub.get("metadata") or {}).get("empresa_id")
    sub = None
    if empresa_id_str:
        sub = _get_or_create_local_subscription(db, uuid.UUID(empresa_id_str))
    else:
        sub = db.scalar(select(Subscription).where(Subscription.stripe_customer_id == stripe_sub.get("customer")))
        if sub is None:
            return None

    itens = (stripe_sub.get("items") or {}).get("data") or []
    price = itens[0]["price"] if itens else None
    price_id = price["id"] if price else stripe_sub.get("plan", {}).get("id")

    sub.stripe_customer_id = stripe_sub.get("customer") or sub.stripe_customer_id
    sub.stripe_subscription_id = stripe_sub.get("id")
    sub.stripe_price_id = price_id
    plano = _price_para_plano(price_id)
    if plano:
        sub.plano = plano
    sub.status = STRIPE_STATUS_MAP.get(stripe_sub.get("status"), sub.status)
    if price and price.get("unit_amount") is not None:
        sub.valor_mensal = Decimal(price["unit_amount"]) / Decimal(100)
    sub.periodo_atual_fim = _timestamp_para_date(_current_period_end(stripe_sub))
    sub.cancelar_ao_fim_periodo = bool(stripe_sub.get("cancel_at_period_end"))
    trial_fim = _timestamp_para_date(stripe_sub.get("trial_end"))
    if trial_fim:
        sub.trial_fim = trial_fim
    inicio = _timestamp_para_date(stripe_sub.get("start_date"))
    if inicio and not sub.data_inicio:
        sub.data_inicio = inicio
    if sub.status in (StatusAssinatura.CANCELED, StatusAssinatura.UNPAID):
        sub.data_fim = sub.data_fim or date.today()
    else:
        sub.data_fim = None

    db.commit()
    return sub


def sincronizar_fatura(db: Session, stripe_invoice: dict) -> Fatura | None:
    empresa_id_str = (stripe_invoice.get("subscription_details") or {}).get("metadata", {}).get("empresa_id")
    sub = None
    if not empresa_id_str:
        sub = db.scalar(select(Subscription).where(Subscription.stripe_customer_id == stripe_invoice.get("customer")))
        if sub is None:
            return None
        empresa_id = sub.empresa_id
    else:
        empresa_id = uuid.UUID(empresa_id_str)
        sub = db.scalar(select(Subscription).where(Subscription.empresa_id == empresa_id))

    stripe_status = stripe_invoice.get("status")
    if stripe_invoice.get("amount_remaining", 0) == 0 and stripe_status == "paid":
        status = StatusFatura.PAGA
    elif stripe_status in ("open", "draft"):
        status = StatusFatura.PENDENTE
    elif stripe_status == "uncollectible":
        status = StatusFatura.FALHOU
    elif stripe_status == "void":
        status = StatusFatura.REEMBOLSADA
    else:
        status = StatusFatura.PENDENTE

    fatura = db.scalar(select(Fatura).where(Fatura.stripe_invoice_id == stripe_invoice["id"]))
    if fatura is None:
        fatura = Fatura(empresa_id=empresa_id, stripe_invoice_id=stripe_invoice["id"], status=status)
        db.add(fatura)

    linhas = (stripe_invoice.get("lines") or {}).get("data") or []
    periodo = linhas[0].get("period") if linhas else None

    fatura.subscription_id = sub.id if sub else fatura.subscription_id
    fatura.stripe_customer_id = stripe_invoice.get("customer")
    fatura.numero = stripe_invoice.get("number")
    fatura.valor_total = Decimal(stripe_invoice.get("amount_due", 0)) / Decimal(100)
    fatura.valor_pago = Decimal(stripe_invoice.get("amount_paid", 0)) / Decimal(100)
    fatura.moeda = stripe_invoice.get("currency", "brl")
    fatura.status = status
    if periodo:
        fatura.periodo_inicio = _timestamp_para_date(periodo.get("start"))
        fatura.periodo_fim = _timestamp_para_date(periodo.get("end"))
    fatura.url_fatura = stripe_invoice.get("hosted_invoice_url")
    fatura.url_pdf = stripe_invoice.get("invoice_pdf")
    if status == StatusFatura.PAGA:
        fatura.pago_em = _timestamp_para_datetime(stripe_invoice.get("status_transitions", {}).get("paid_at")) or datetime.now(timezone.utc)

    db.commit()
    return fatura


def registrar_reembolso(db: Session, stripe_refund: dict) -> Reembolso | None:
    fatura = None
    payment_intent = stripe_refund.get("payment_intent")
    if payment_intent:
        invoice = stripe.Invoice.list(payment_intent=payment_intent, limit=1)
        if invoice.data:
            fatura = db.scalar(select(Fatura).where(Fatura.stripe_invoice_id == invoice.data[0]["id"]))

    if fatura is None:
        return None

    existente = db.scalar(select(Reembolso).where(Reembolso.stripe_refund_id == stripe_refund["id"]))
    if existente:
        return existente

    reembolso = Reembolso(
        empresa_id=fatura.empresa_id,
        fatura_id=fatura.id,
        stripe_refund_id=stripe_refund["id"],
        stripe_payment_intent_id=payment_intent,
        valor=Decimal(stripe_refund.get("amount", 0)) / Decimal(100),
        motivo=stripe_refund.get("reason"),
        status=stripe_refund.get("status", "unknown"),
    )
    db.add(reembolso)
    fatura.status = StatusFatura.REEMBOLSADA
    db.commit()
    return reembolso


def evento_ja_processado(db: Session, stripe_event_id: str) -> bool:
    evento = db.scalar(select(EventoStripe).where(EventoStripe.stripe_event_id == stripe_event_id))
    return evento is not None and evento.processado


def registrar_evento(db: Session, stripe_event_id: str, tipo_evento: str) -> EventoStripe:
    evento = db.scalar(select(EventoStripe).where(EventoStripe.stripe_event_id == stripe_event_id))
    if evento is None:
        evento = EventoStripe(stripe_event_id=stripe_event_id, tipo_evento=tipo_evento)
        db.add(evento)
        db.commit()
    return evento


def marcar_evento_processado(db: Session, evento: EventoStripe, erro: str | None = None) -> None:
    evento.processado = erro is None
    evento.processado_em = datetime.now(timezone.utc)
    evento.erro = erro
    db.commit()
