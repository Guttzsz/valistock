import enum

from app.models.usuario import PerfilUsuario


class Permissao(str, enum.Enum):
    PRODUTOS_VISUALIZAR = "produtos.visualizar"
    PRODUTOS_CRIAR = "produtos.criar"
    PRODUTOS_EDITAR = "produtos.editar"
    PRODUTOS_EXCLUIR = "produtos.excluir"
    LOTES_VISUALIZAR = "lotes.visualizar"
    LOTES_CRIAR = "lotes.criar"
    LOTES_EDITAR = "lotes.editar"
    PERDAS_VISUALIZAR = "perdas.visualizar"
    PERDAS_REGISTRAR = "perdas.registrar"
    RELATORIOS_VISUALIZAR = "relatorios.visualizar"
    RELATORIOS_EXPORTAR = "relatorios.exportar"
    FUNCIONARIOS_GERENCIAR = "funcionarios.gerenciar"
    CATEGORIAS_GERENCIAR = "categorias.gerenciar"
    FORNECEDORES_GERENCIAR = "fornecedores.gerenciar"
    LOCALIZACOES_GERENCIAR = "localizacoes.gerenciar"
    CONFIGURACOES_GERENCIAR = "configuracoes.gerenciar"
    ASSINATURA_GERENCIAR = "assinatura.gerenciar"
    EMPRESA_GERENCIAR = "empresa.gerenciar"
    AUDITORIA_VISUALIZAR = "auditoria.visualizar"


_TODAS = set(Permissao)

_GERENTE = _TODAS - {
    Permissao.FUNCIONARIOS_GERENCIAR,
    Permissao.EMPRESA_GERENCIAR,
    Permissao.ASSINATURA_GERENCIAR,
}

_FUNCIONARIO = {
    Permissao.PRODUTOS_VISUALIZAR,
    Permissao.PRODUTOS_CRIAR,
    Permissao.PRODUTOS_EDITAR,
    Permissao.LOTES_VISUALIZAR,
    Permissao.LOTES_CRIAR,
    Permissao.LOTES_EDITAR,
    Permissao.PERDAS_VISUALIZAR,
    Permissao.PERDAS_REGISTRAR,
}

# Matriz central perfil -> permissoes. Unica fonte de verdade: nunca espalhar checagens ad-hoc.
PERMISSOES_POR_PERFIL: dict[PerfilUsuario, set[Permissao]] = {
    PerfilUsuario.ADMINISTRADOR: _TODAS,
    PerfilUsuario.GERENTE: _GERENTE,
    PerfilUsuario.FUNCIONARIO: _FUNCIONARIO,
}


def tem_permissao(perfil: PerfilUsuario, permissao: Permissao) -> bool:
    return permissao in PERMISSOES_POR_PERFIL.get(perfil, set())


def permissoes_do_perfil(perfil: PerfilUsuario) -> list[str]:
    return sorted(p.value for p in PERMISSOES_POR_PERFIL.get(perfil, set()))
