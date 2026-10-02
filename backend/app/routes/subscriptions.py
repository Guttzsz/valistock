from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.config import get_settings
from app.database import get_db
from app.models.empresa import Empresa
from app.models.fatura import Fatura
from app.models.produto import Produto
from app.models.subscription import StatusAssinatura, Subscription
from app.models.usuario import Usuario
from app.schemas.subscription import CheckoutRequest, CheckoutResponse, FaturaOut, PortalResponse, SubscriptionOut
from app.services import stripe_service
from app.services.auditoria_service import registrar_auditoria
from app.services.plano_service import LIMITES, get_plano_atual
from app.utils.exceptions import ValidationErrorApp

settings = get_settings()

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


def _montar_subscription_out(db: Session, empresa_id) -> SubscriptionOut:
    plano = get_plano_atual(db, empresa_id)
    sub = db.scalar(select(Subscription).where(Subscription.empresa_id == empresa_id))
    limites = LIMITES[plano]
    produtos_usados = db.scalar(select(func.count()).select_from(Produto).where(Produto.empresa_id == empresa_id))
    usuarios_usados = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.empresa_id == empresa_id))
    return SubscriptionOut(
        plano=plano,
        status=sub.status if sub else StatusAssinatura.ACTIVE,
        limite_produtos=limites["products"],
        limite_usuarios=limites["users"],
        produtos_usados=produtos_usados or 0,
        usuarios_usados=usuarios_usados or 0,
        valor_mensal=sub.valor_mensal if sub else 0,
        periodo_atual_fim=sub.periodo_atual_fim if sub else None,
        trial_fim=sub.trial_fim if sub else None,
        cancelar_ao_fim_periodo=sub.cancelar_ao_fim_periodo if sub else False,
        possui_stripe=bool(sub and sub.stripe_customer_id),
    )


@router.get("/atual", response_model=SubscriptionOut)
def obter_assinatura_atual(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _montar_subscription_out(db, current_user.empresa_id)


@router.get("/faturas", response_model=list[FaturaOut])
def listar_faturas(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Fatura).where(Fatura.empresa_id == current_user.empresa_id).order_by(Fatura.criado_em.desc()).limit(24)
    return db.scalars(stmt).all()


@router.post("/checkout", response_model=CheckoutResponse)
def criar_checkout(
    payload: CheckoutRequest, current_user: CurrentUser = Depends(require_permissao(Permissao.ASSINATURA_GERENCIAR)), db: Session = Depends(get_db)
):
    price_map = {
        "essencial": settings.stripe_price_essencial,
        "profissional": settings.stripe_price_profissional,
        "empresa": settings.stripe_price_empresa,
    }
    price_id = price_map.get(payload.plano)
    if not price_id:
        raise ValidationErrorApp("Plano invalido. Escolha 'essencial', 'profissional' ou 'empresa'.")
    if not settings.stripe_secret_key:
        raise ValidationErrorApp("Pagamentos ainda nao configurados neste ambiente.")

    empresa = db.get(Empresa, current_user.empresa_id)
    url = stripe_service.criar_checkout_session(db, empresa, price_id)
    return CheckoutResponse(url=url)


@router.post("/portal", response_model=PortalResponse)
def criar_portal(current_user: CurrentUser = Depends(require_permissao(Permissao.ASSINATURA_GERENCIAR)), db: Session = Depends(get_db)):
    empresa = db.get(Empresa, current_user.empresa_id)
    url = stripe_service.criar_portal_session(db, empresa)
    return PortalResponse(url=url)


@router.post("/cancelar", response_model=SubscriptionOut)
def cancelar_assinatura(current_user: CurrentUser = Depends(require_permissao(Permissao.ASSINATURA_GERENCIAR)), db: Session = Depends(get_db)):
    empresa = db.get(Empresa, current_user.empresa_id)
    stripe_service.cancelar_assinatura(db, empresa)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "assinatura.cancelada", "assinatura", None, f"{current_user.nome} cancelou a assinatura (efetiva no fim do periodo ja pago).",
    )
    db.commit()
    return _montar_subscription_out(db, current_user.empresa_id)


@router.post("/reativar", response_model=SubscriptionOut)
def reativar_assinatura(current_user: CurrentUser = Depends(require_permissao(Permissao.ASSINATURA_GERENCIAR)), db: Session = Depends(get_db)):
    empresa = db.get(Empresa, current_user.empresa_id)
    stripe_service.reativar_assinatura(db, empresa)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "assinatura.reativada", "assinatura", None, f"{current_user.nome} reativou a assinatura.",
    )
    db.commit()
    return _montar_subscription_out(db, current_user.empresa_id)
