from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.models.subscription import PlanoNome, Subscription
from app.models.usuario import Usuario
from app.utils.exceptions import PlanLimitError

# Centralized plan limits. Nunca espalhar regras de plano pelo resto do codigo.
LIMITES = {
    PlanoNome.GRATUITO: {"products": 50, "users": 3, "reports": False},
    PlanoNome.BASICO: {"products": 500, "users": 15, "reports": True},
    PlanoNome.PROFISSIONAL: {"products": None, "users": None, "reports": True},  # None = ilimitado
}


def get_plano_atual(db: Session, empresa_id) -> PlanoNome:
    sub = db.scalar(select(Subscription).where(Subscription.empresa_id == empresa_id))
    return sub.plano if sub else PlanoNome.GRATUITO


def check_plan_limit(db: Session, empresa_id, recurso: str) -> None:
    """Raises PlanLimitError if the company's current plan does not allow one more of `recurso`."""
    plano = get_plano_atual(db, empresa_id)
    limites = LIMITES[plano]

    if recurso == "products":
        limite = limites["products"]
        if limite is not None:
            total = db.scalar(select(func.count()).select_from(Produto).where(Produto.empresa_id == empresa_id))
            if total >= limite:
                raise PlanLimitError(f"Seu plano ({plano.value}) permite ate {limite} produtos. Faca upgrade para continuar.")
    elif recurso == "users":
        limite = limites["users"]
        if limite is not None:
            total = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.empresa_id == empresa_id))
            if total >= limite:
                raise PlanLimitError(f"Seu plano ({plano.value}) permite ate {limite} usuarios. Faca upgrade para continuar.")
    elif recurso == "reports":
        if not limites["reports"]:
            raise PlanLimitError(f"Relatorios avancados nao estao disponiveis no plano {plano.value}. Faca upgrade para continuar.")
