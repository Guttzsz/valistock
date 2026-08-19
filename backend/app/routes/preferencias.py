import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.preferencia import WIDGETS_PADRAO, PreferenciaDashboard, PreferenciaNotificacao
from app.schemas.preferencia import (
    PreferenciaDashboardIn,
    PreferenciaDashboardOut,
    PreferenciaNotificacaoIn,
    PreferenciaNotificacaoOut,
)

router = APIRouter(prefix="/api/preferencias", tags=["preferencias"])

WIDGETS_VALIDOS = {
    "produtos_cadastrados", "proximos_vencimento", "vencidos", "valor_em_risco",
    "perdas_do_mes", "economia_potencial", "estoque_baixo", "produtos_mais_perdidos",
    "categorias_mais_perdas", "grafico_perdas", "grafico_risco",
}


@router.get("/notificacoes", response_model=PreferenciaNotificacaoOut)
def obter_preferencias_notificacao(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.scalar(select(PreferenciaNotificacao).where(PreferenciaNotificacao.usuario_id == current_user.id))
    if pref is None:
        pref = PreferenciaNotificacao(id=uuid.uuid4(), usuario_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("/notificacoes", response_model=PreferenciaNotificacaoOut)
def atualizar_preferencias_notificacao(
    payload: PreferenciaNotificacaoIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    pref = db.scalar(select(PreferenciaNotificacao).where(PreferenciaNotificacao.usuario_id == current_user.id))
    if pref is None:
        pref = PreferenciaNotificacao(id=uuid.uuid4(), usuario_id=current_user.id)
        db.add(pref)
    for campo, valor in payload.model_dump().items():
        setattr(pref, campo, valor)
    db.commit()
    db.refresh(pref)
    return pref


@router.get("/dashboard", response_model=PreferenciaDashboardOut)
def obter_preferencias_dashboard(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.scalar(select(PreferenciaDashboard).where(PreferenciaDashboard.usuario_id == current_user.id))
    if pref is None or not pref.widgets_ativos:
        return PreferenciaDashboardOut(widgets_ativos=WIDGETS_PADRAO)
    return PreferenciaDashboardOut(widgets_ativos=json.loads(pref.widgets_ativos))


@router.put("/dashboard", response_model=PreferenciaDashboardOut)
def atualizar_preferencias_dashboard(
    payload: PreferenciaDashboardIn, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    widgets = [w for w in payload.widgets_ativos if w in WIDGETS_VALIDOS]
    pref = db.scalar(select(PreferenciaDashboard).where(PreferenciaDashboard.usuario_id == current_user.id))
    if pref is None:
        pref = PreferenciaDashboard(id=uuid.uuid4(), usuario_id=current_user.id, widgets_ativos=json.dumps(widgets))
        db.add(pref)
    else:
        pref.widgets_ativos = json.dumps(widgets)
    db.commit()
    return PreferenciaDashboardOut(widgets_ativos=widgets)
