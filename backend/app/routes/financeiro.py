from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, require_super_admin
from app.database import get_db
from app.models.empresa import Empresa
from app.models.fatura import Fatura, StatusFatura
from app.models.subscription import PlanoNome, StatusAssinatura, Subscription
from app.schemas.financeiro import (
    AssinaturaAdminOut,
    FinanceiroDashboardOut,
    PagamentoAdminOut,
    ReceitaPorMes,
    ReceitaPorPlano,
)
from app.services import stripe_service
from app.utils.exceptions import NotFoundError
from app.utils.timezone import today

router = APIRouter(prefix="/api/financeiro", tags=["financeiro"])

PLANOS_PAGOS = (PlanoNome.ESSENCIAL, PlanoNome.PROFISSIONAL, PlanoNome.EMPRESA, PlanoNome.REDE)


@router.get("/dashboard", response_model=FinanceiroDashboardOut)
def obter_dashboard_financeiro(current_user: CurrentUser = Depends(require_super_admin), db: Session = Depends(get_db)):
    hoje = today()
    inicio_mes = hoje.replace(day=1)
    inicio_ano = hoje.replace(month=1, day=1)

    assinaturas = db.scalars(select(Subscription)).all()

    ativas = [s for s in assinaturas if s.status == StatusAssinatura.ACTIVE]
    trials = [s for s in assinaturas if s.status == StatusAssinatura.TRIALING]
    inadimplentes = [s for s in assinaturas if s.status in (StatusAssinatura.PAST_DUE, StatusAssinatura.UNPAID)]
    pagantes = [s for s in ativas if s.plano in PLANOS_PAGOS]
    cancelamentos_periodo = [
        s for s in assinaturas if s.status == StatusAssinatura.CANCELED and s.data_fim and s.data_fim >= inicio_mes
    ]

    mrr = sum((s.valor_mensal for s in pagantes), Decimal(0))
    arr = mrr * 12

    receita_mensal = db.scalar(
        select(func.coalesce(func.sum(Fatura.valor_pago), 0)).where(Fatura.status == StatusFatura.PAGA, Fatura.pago_em >= inicio_mes)
    ) or Decimal(0)
    receita_anual = db.scalar(
        select(func.coalesce(func.sum(Fatura.valor_pago), 0)).where(Fatura.status == StatusFatura.PAGA, Fatura.pago_em >= inicio_ano)
    ) or Decimal(0)

    arpu = (mrr / len(pagantes)) if pagantes else None

    return FinanceiroDashboardOut(
        receita_mensal=Decimal(receita_mensal),
        receita_anual=Decimal(receita_anual),
        mrr=mrr,
        arr=arr,
        assinaturas_ativas=len(ativas),
        clientes_pagantes=len(pagantes),
        trials=len(trials),
        cancelamentos_periodo=len(cancelamentos_periodo),
        inadimplencia=len(inadimplentes),
        arpu=arpu,
    )


@router.get("/receita-mensal", response_model=list[ReceitaPorMes])
def obter_receita_mensal(current_user: CurrentUser = Depends(require_super_admin), db: Session = Depends(get_db)):
    inicio = today().replace(day=1) - timedelta(days=365)
    faturas = db.scalars(select(Fatura).where(Fatura.status == StatusFatura.PAGA, Fatura.pago_em >= inicio)).all()

    baldes: "OrderedDict[str, Decimal]" = OrderedDict()
    cursor = inicio.replace(day=1)
    hoje = today()
    while cursor <= hoje:
        baldes[cursor.strftime("%Y-%m")] = Decimal(0)
        cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

    for fatura in faturas:
        if not fatura.pago_em:
            continue
        chave = fatura.pago_em.strftime("%Y-%m")
        if chave in baldes:
            baldes[chave] += fatura.valor_pago

    return [ReceitaPorMes(mes=mes, receita=valor) for mes, valor in baldes.items()]


@router.get("/receita-por-plano", response_model=list[ReceitaPorPlano])
def obter_receita_por_plano(current_user: CurrentUser = Depends(require_super_admin), db: Session = Depends(get_db)):
    assinaturas = db.scalars(select(Subscription).where(Subscription.status == StatusAssinatura.ACTIVE)).all()
    mrr_total = sum((s.valor_mensal for s in assinaturas if s.plano in PLANOS_PAGOS), Decimal(0))

    resultado = []
    for plano in PlanoNome:
        do_plano = [s for s in assinaturas if s.plano == plano]
        receita = sum((s.valor_mensal for s in do_plano), Decimal(0))
        percentual = (receita / mrr_total * 100) if mrr_total > 0 else Decimal(0)
        resultado.append(ReceitaPorPlano(plano=plano, quantidade=len(do_plano), receita_mensal=receita, percentual=round(percentual, 1)))
    return resultado


@router.get("/assinaturas", response_model=list[AssinaturaAdminOut])
def listar_assinaturas(current_user: CurrentUser = Depends(require_super_admin), db: Session = Depends(get_db)):
    stmt = select(Subscription, Empresa.nome_fantasia).join(Empresa, Empresa.id == Subscription.empresa_id).order_by(Subscription.criado_em.desc())
    resultado = []
    for sub, nome_empresa in db.execute(stmt).all():
        resultado.append(
            AssinaturaAdminOut(
                empresa_id=sub.empresa_id,
                empresa_nome=nome_empresa,
                plano=sub.plano,
                status=sub.status,
                valor_mensal=sub.valor_mensal,
                data_inicio=sub.data_inicio,
                periodo_atual_fim=sub.periodo_atual_fim,
                stripe_customer_id=sub.stripe_customer_id,
                stripe_subscription_id=sub.stripe_subscription_id,
            )
        )
    return resultado


@router.get("/pagamentos", response_model=list[PagamentoAdminOut])
def listar_pagamentos(current_user: CurrentUser = Depends(require_super_admin), db: Session = Depends(get_db)):
    stmt = select(Fatura, Empresa.nome_fantasia).join(Empresa, Empresa.id == Fatura.empresa_id).order_by(Fatura.criado_em.desc()).limit(100)
    resultado = []
    for fatura, nome_empresa in db.execute(stmt).all():
        resultado.append(
            PagamentoAdminOut(
                id=fatura.id,
                empresa_nome=nome_empresa,
                numero=fatura.numero,
                valor_total=fatura.valor_total,
                status=fatura.status,
                criado_em=fatura.criado_em,
                url_fatura=fatura.url_fatura,
            )
        )
    return resultado


@router.post("/sincronizar/{empresa_id}")
def sincronizar_empresa(empresa_id: str, current_user: CurrentUser = Depends(require_super_admin), db: Session = Depends(get_db)):
    """Sincronizacao manual sob demanda (nao deve ser usada como rotina - webhooks ja mantem tudo atualizado)."""
    import stripe

    sub = db.scalar(select(Subscription).where(Subscription.empresa_id == empresa_id))
    if sub is None or not sub.stripe_subscription_id:
        raise NotFoundError("Esta empresa nao possui assinatura no Stripe.")

    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
    stripe_service.sincronizar_subscription(db, stripe_sub.to_dict())
    return {"sincronizado": True}
