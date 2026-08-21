from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alerta import Alerta, TipoAlerta
from app.models.configuracao import Configuracao
from app.models.empresa import Empresa
from app.models.lote import Lote, StatusLote
from app.models.produto import Produto
from app.services.push_service import enviar_push_para_empresa
from app.services.validade_service import dias_restantes
from app.utils.timezone import today


def _get_or_create_configuracao(db: Session, empresa_id) -> Configuracao:
    config = db.scalar(select(Configuracao).where(Configuracao.empresa_id == empresa_id))
    if config is None:
        config = Configuracao(empresa_id=empresa_id)
        db.add(config)
        db.flush()
    return config


def _tipo_para_dias(dias: int, config: Configuracao) -> TipoAlerta | None:
    if dias < 0:
        return TipoAlerta.VENCIDO
    if dias == 0:
        return TipoAlerta.VENCE_HOJE
    if dias == config.dias_alerta_3:
        return TipoAlerta.VENCIMENTO_1_DIA
    if dias == config.dias_alerta_2:
        return TipoAlerta.VENCIMENTO_3_DIAS
    if dias == config.dias_alerta_1:
        return TipoAlerta.VENCIMENTO_7_DIAS
    return None


def _mensagem(tipo: TipoAlerta, produto_nome: str, quantidade: int, dias: int) -> str:
    if tipo == TipoAlerta.VENCIDO:
        return f"{produto_nome} possui produtos vencidos."
    if tipo == TipoAlerta.VENCE_HOJE:
        return f"Urgente: {produto_nome} vence hoje."
    if tipo == TipoAlerta.VENCIMENTO_1_DIA:
        return f"Urgente: {produto_nome} vence amanha."
    if tipo == TipoAlerta.VENCIMENTO_3_DIAS:
        return f"Atencao: {produto_nome} vence em {dias} dias."
    if tipo == TipoAlerta.VENCIMENTO_7_DIAS:
        return f"{produto_nome} possui {quantidade} unidades vencendo em {dias} dias."
    return f"Estoque baixo: {produto_nome}."


def _titulo_para_tipo(tipo: TipoAlerta) -> str:
    if tipo == TipoAlerta.ESTOQUE_BAIXO:
        return "Estoque baixo"
    if tipo in (TipoAlerta.VENCIDO, TipoAlerta.VENCE_HOJE, TipoAlerta.VENCIMENTO_1_DIA):
        return "Alerta urgente de validade"
    return "Alerta de validade"


def _criar_alerta_se_necessario(db: Session, empresa_id, produto: Produto, lote: Lote | None, tipo: TipoAlerta, mensagem: str) -> bool:
    filtros = [Alerta.empresa_id == empresa_id, Alerta.produto_id == produto.id, Alerta.tipo == tipo]
    if lote is not None:
        filtros.append(Alerta.lote_id == lote.id)
    else:
        filtros.append(Alerta.lote_id.is_(None))
    filtros.append(Alerta.data_alerta == today())

    existente = db.scalar(select(Alerta).where(*filtros))
    if existente is not None:
        return False

    db.add(
        Alerta(
            empresa_id=empresa_id,
            produto_id=produto.id,
            lote_id=lote.id if lote else None,
            tipo=tipo,
            mensagem=mensagem,
            data_alerta=today(),
        )
    )
    enviar_push_para_empresa(db, empresa_id, _titulo_para_tipo(tipo), mensagem)
    return True


def verificar_vencimentos_empresa(db: Session, empresa_id) -> int:
    """Scans all active lotes of a company, updates lote status, and raises alerts. Returns alerts created."""
    config = _get_or_create_configuracao(db, empresa_id)
    lotes = db.scalars(
        select(Lote).where(
            Lote.empresa_id == empresa_id,
            Lote.status.in_([StatusLote.ATIVO, StatusLote.PROXIMO_VENCIMENTO, StatusLote.VENCIDO]),
        )
    ).all()

    alertas_criados = 0
    for lote in lotes:
        dias = dias_restantes(lote.data_validade)
        produto = db.get(Produto, lote.produto_id)
        if produto is None:
            continue

        if dias < 0:
            lote.status = StatusLote.VENCIDO
        elif dias <= config.dias_alerta_1:
            lote.status = StatusLote.PROXIMO_VENCIMENTO
        else:
            lote.status = StatusLote.ATIVO

        tipo = _tipo_para_dias(dias, config)
        if tipo is not None:
            mensagem = _mensagem(tipo, produto.nome, lote.quantidade, dias)
            if _criar_alerta_se_necessario(db, empresa_id, produto, lote, tipo, mensagem):
                alertas_criados += 1

    produtos = db.scalars(select(Produto).where(Produto.empresa_id == empresa_id, Produto.ativo.is_(True))).all()
    for produto in produtos:
        if produto.estoque_atual <= produto.estoque_minimo:
            mensagem = f"Estoque baixo: {produto.nome} possui {produto.estoque_atual} unidades (minimo {produto.estoque_minimo})."
            if _criar_alerta_se_necessario(db, empresa_id, produto, None, TipoAlerta.ESTOQUE_BAIXO, mensagem):
                alertas_criados += 1

    db.commit()
    return alertas_criados


def verificar_vencimentos_todas_empresas(db: Session) -> None:
    empresa_ids = db.scalars(select(Empresa.id).where(Empresa.ativo.is_(True))).all()
    for empresa_id in empresa_ids:
        verificar_vencimentos_empresa(db, empresa_id)
