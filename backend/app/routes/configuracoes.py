import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_admin, require_permissao
from app.auth.permissions import Permissao
from app.models.categoria import Categoria
from app.database import get_db
from app.models.configuracao import Configuracao
from app.schemas.configuracao import ConfiguracaoAlertasUpdate, ConfiguracaoEmpresaUpdate, ConfiguracaoOut, OnboardingEtapaUpdate
from app.services.auditoria_service import registrar_auditoria

router = APIRouter(prefix="/api/configuracoes", tags=["configuracoes"])


def _get_or_create(db: Session, empresa_id) -> Configuracao:
    config = db.scalar(select(Configuracao).where(Configuracao.empresa_id == empresa_id))
    if config is None:
        config = Configuracao(empresa_id=empresa_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ConfiguracaoOut)
def obter_configuracoes(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_or_create(db, current_user.empresa_id)


@router.put("/alertas", response_model=ConfiguracaoOut)
def atualizar_alertas(
    payload: ConfiguracaoAlertasUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CONFIGURACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    config = _get_or_create(db, current_user.empresa_id)
    config.dias_alerta_1 = payload.dias_alerta_1
    config.dias_alerta_2 = payload.dias_alerta_2
    config.dias_alerta_3 = payload.dias_alerta_3
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "configuracao.alertas_atualizada", "configuracao", None, f"{current_user.nome} alterou os prazos de alerta.",
    )
    db.commit()
    db.refresh(config)
    return config


@router.put("/empresa", response_model=ConfiguracaoOut)
def atualizar_configuracao_empresa(
    payload: ConfiguracaoEmpresaUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CONFIGURACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    config = _get_or_create(db, current_user.empresa_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(config, campo, valor)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "configuracao.empresa_atualizada", "configuracao", None, f"{current_user.nome} alterou as configuracoes do estabelecimento.",
    )
    db.commit()
    db.refresh(config)
    return config


@router.put("/onboarding", response_model=ConfiguracaoOut)
def atualizar_onboarding(
    payload: OnboardingEtapaUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Avanca o fluxo guiado de configuracao inicial. Cada etapa persiste no banco - nunca so no localStorage."""
    config = _get_or_create(db, current_user.empresa_id)
    config.onboarding_etapa = payload.etapa

    if payload.tipo_estabelecimento:
        config.tipo_estabelecimento = (
            payload.tipo_estabelecimento_outro if payload.tipo_estabelecimento == "outro" and payload.tipo_estabelecimento_outro
            else payload.tipo_estabelecimento
        )
    if payload.quantidade_funcionarios_aprox:
        config.quantidade_funcionarios_aprox = payload.quantidade_funcionarios_aprox
    if payload.quantidade_produtos_aprox:
        config.quantidade_produtos_aprox = payload.quantidade_produtos_aprox
    if payload.dias_alerta_1:
        config.dias_alerta_1 = payload.dias_alerta_1
    if payload.dias_alerta_2:
        config.dias_alerta_2 = payload.dias_alerta_2
    if payload.dias_alerta_3:
        config.dias_alerta_3 = payload.dias_alerta_3

    if payload.categorias_iniciais:
        existentes = {
            c.nome for c in db.scalars(select(Categoria).where(Categoria.empresa_id == current_user.empresa_id)).all()
        }
        for nome in payload.categorias_iniciais:
            nome = nome.strip()
            if nome and nome not in existentes:
                db.add(Categoria(id=uuid.uuid4(), empresa_id=current_user.empresa_id, nome=nome))
                existentes.add(nome)

    if payload.concluir:
        config.onboarding_concluido = True
        registrar_auditoria(
            db, current_user.empresa_id, current_user.id, current_user.nome,
            "onboarding.concluido", "configuracao", None, f"{current_user.nome} concluiu a configuracao inicial do estabelecimento.",
        )

    db.commit()
    db.refresh(config)
    return config
