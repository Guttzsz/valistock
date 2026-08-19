import json
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user, require_permissao
from app.auth.permissions import Permissao
from app.database import get_db
from app.models.campo_personalizado import CampoPersonalizado, ValorCampoPersonalizado
from app.models.produto import Produto
from app.schemas.campo_personalizado import (
    CampoPersonalizadoCreate,
    CampoPersonalizadoOut,
    CampoPersonalizadoUpdate,
    ValorCampoPersonalizadoIn,
    ValorCampoPersonalizadoOut,
)
from app.services.auditoria_service import registrar_auditoria
from app.utils.exceptions import NotFoundError, ValidationErrorApp

router = APIRouter(tags=["campos-personalizados"])


def _out(campo: CampoPersonalizado) -> CampoPersonalizadoOut:
    return CampoPersonalizadoOut(
        id=campo.id, nome=campo.nome, tipo=campo.tipo, obrigatorio=campo.obrigatorio,
        opcoes=json.loads(campo.opcoes) if campo.opcoes else None, ativo=campo.ativo, criado_em=campo.criado_em,
    )


@router.get("/api/campos-personalizados", response_model=list[CampoPersonalizadoOut])
def listar_campos(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(CampoPersonalizado).where(CampoPersonalizado.empresa_id == current_user.empresa_id, CampoPersonalizado.ativo.is_(True))
    return [_out(c) for c in db.scalars(stmt).all()]


@router.post("/api/campos-personalizados", response_model=CampoPersonalizadoOut, status_code=201)
def criar_campo(
    payload: CampoPersonalizadoCreate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CONFIGURACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    dados = payload.model_dump()
    opcoes = dados.pop("opcoes")
    campo = CampoPersonalizado(id=uuid.uuid4(), empresa_id=current_user.empresa_id, opcoes=json.dumps(opcoes) if opcoes else None, **dados)
    db.add(campo)
    registrar_auditoria(
        db, current_user.empresa_id, current_user.id, current_user.nome,
        "campo_personalizado.criado", "campo_personalizado", campo.id, f"{current_user.nome} criou o campo personalizado {campo.nome}.",
    )
    db.commit()
    db.refresh(campo)
    return _out(campo)


def _get_campo_da_empresa(db: Session, campo_id: UUID, empresa_id: UUID) -> CampoPersonalizado:
    campo = db.scalar(select(CampoPersonalizado).where(CampoPersonalizado.id == campo_id, CampoPersonalizado.empresa_id == empresa_id))
    if campo is None:
        raise NotFoundError("Campo personalizado nao encontrado.")
    return campo


@router.put("/api/campos-personalizados/{campo_id}", response_model=CampoPersonalizadoOut)
def atualizar_campo(
    campo_id: UUID,
    payload: CampoPersonalizadoUpdate,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CONFIGURACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    campo = _get_campo_da_empresa(db, campo_id, current_user.empresa_id)
    dados = payload.model_dump(exclude_unset=True)
    if "opcoes" in dados:
        dados["opcoes"] = json.dumps(dados["opcoes"]) if dados["opcoes"] else None
    for campo_nome, valor in dados.items():
        setattr(campo, campo_nome, valor)
    db.commit()
    db.refresh(campo)
    return _out(campo)


@router.delete("/api/campos-personalizados/{campo_id}", status_code=204)
def desativar_campo(
    campo_id: UUID,
    current_user: CurrentUser = Depends(require_permissao(Permissao.CONFIGURACOES_GERENCIAR)),
    db: Session = Depends(get_db),
):
    campo = _get_campo_da_empresa(db, campo_id, current_user.empresa_id)
    campo.ativo = False
    db.commit()
    return None


@router.get("/api/produtos/{produto_id}/campos-personalizados", response_model=list[ValorCampoPersonalizadoOut])
def obter_valores_produto(produto_id: UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    produto = db.scalar(select(Produto).where(Produto.id == produto_id, Produto.empresa_id == current_user.empresa_id))
    if produto is None:
        raise NotFoundError("Produto nao encontrado.")

    campos = db.scalars(
        select(CampoPersonalizado).where(CampoPersonalizado.empresa_id == current_user.empresa_id, CampoPersonalizado.ativo.is_(True))
    ).all()
    valores = {
        v.campo_id: v.valor
        for v in db.scalars(select(ValorCampoPersonalizado).where(ValorCampoPersonalizado.produto_id == produto_id)).all()
    }
    return [
        ValorCampoPersonalizadoOut(campo_id=c.id, nome=c.nome, tipo=c.tipo, valor=valores.get(c.id))
        for c in campos
    ]


@router.put("/api/produtos/{produto_id}/campos-personalizados", response_model=list[ValorCampoPersonalizadoOut])
def definir_valores_produto(
    produto_id: UUID,
    payload: list[ValorCampoPersonalizadoIn],
    current_user: CurrentUser = Depends(require_permissao(Permissao.PRODUTOS_EDITAR)),
    db: Session = Depends(get_db),
):
    produto = db.scalar(select(Produto).where(Produto.id == produto_id, Produto.empresa_id == current_user.empresa_id))
    if produto is None:
        raise NotFoundError("Produto nao encontrado.")

    for item in payload:
        campo = db.scalar(
            select(CampoPersonalizado).where(CampoPersonalizado.id == item.campo_id, CampoPersonalizado.empresa_id == current_user.empresa_id)
        )
        if campo is None:
            raise ValidationErrorApp("Campo personalizado invalido.")
        if campo.obrigatorio and not item.valor:
            raise ValidationErrorApp(f"O campo '{campo.nome}' e obrigatorio.")

        existente = db.scalar(
            select(ValorCampoPersonalizado).where(
                ValorCampoPersonalizado.campo_id == item.campo_id, ValorCampoPersonalizado.produto_id == produto_id
            )
        )
        if existente:
            existente.valor = item.valor
        else:
            db.add(ValorCampoPersonalizado(id=uuid.uuid4(), campo_id=item.campo_id, produto_id=produto_id, valor=item.valor))

    db.commit()
    return obter_valores_produto(produto_id, current_user, db)
