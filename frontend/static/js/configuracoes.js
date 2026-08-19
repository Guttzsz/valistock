initNav("mais");

async function carregarConfig() {
  try {
    const config = await Api.configuracoes.get();
    document.getElementById("dias-alerta-1").value = config.dias_alerta_1;
    document.getElementById("dias-alerta-2").value = config.dias_alerta_2;
    document.getElementById("dias-alerta-3").value = config.dias_alerta_3;
    document.getElementById("config-tipo").value = config.tipo_estabelecimento || "mercado";
    document.getElementById("config-cor").value = config.cor_principal || "#16a34a";
    document.getElementById("config-horario").value = config.horario_funcionamento || "";
  } catch (err) {
    toast(err.message || "Erro ao carregar configuracoes.", "danger");
  }
}

async function carregarEmpresa() {
  try {
    const empresa = await Api.empresa.get();
    document.getElementById("empresa-nome").value = empresa.nome_fantasia || "";
    document.getElementById("empresa-razao").value = empresa.razao_social || "";
    document.getElementById("empresa-cnpj").value = empresa.cnpj || "";
    document.getElementById("empresa-telefone").value = empresa.telefone || "";
    document.getElementById("empresa-endereco").value = empresa.endereco || "";
    document.getElementById("empresa-cidade").value = empresa.cidade || "";
    document.getElementById("empresa-estado").value = empresa.estado || "";
  } catch (err) {
    toast(err.message || "Erro ao carregar dados do estabelecimento.", "danger");
  }
}

async function carregarNotificacoes() {
  try {
    const prefs = await Api.preferencias.getNotificacoes();
    document.getElementById("notif-vencendo").checked = prefs.produtos_vencendo;
    document.getElementById("notif-vencidos").checked = prefs.produtos_vencidos;
    document.getElementById("notif-estoque").checked = prefs.estoque_baixo;
    document.getElementById("notif-perdas").checked = prefs.novas_perdas;
    document.getElementById("notif-relatorios").checked = prefs.relatorios;
    document.getElementById("notif-avisos").checked = prefs.avisos_administrativos;
  } catch (err) {
    toast(err.message || "Erro ao carregar notificacoes.", "danger");
  }
}

function carregarPerfil() {
  const usuario = Auth.getUser();
  if (!usuario) return;
  document.getElementById("perfil-nome").value = usuario.nome;
  document.getElementById("perfil-email").value = usuario.email;
}

document.getElementById("form-config").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Api.configuracoes.atualizarAlertas({
      dias_alerta_1: Number(document.getElementById("dias-alerta-1").value),
      dias_alerta_2: Number(document.getElementById("dias-alerta-2").value),
      dias_alerta_3: Number(document.getElementById("dias-alerta-3").value),
    });
    toast("Prazos de alerta atualizados.");
  } catch (err) {
    toast(err.message || "Voce nao possui permissao para realizar esta acao.", "danger");
  }
});

document.getElementById("form-empresa").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Api.empresa.update({
      nome_fantasia: document.getElementById("empresa-nome").value.trim(),
      razao_social: document.getElementById("empresa-razao").value.trim() || null,
      cnpj: document.getElementById("empresa-cnpj").value.trim() || null,
      telefone: document.getElementById("empresa-telefone").value.trim() || null,
      endereco: document.getElementById("empresa-endereco").value.trim() || null,
      cidade: document.getElementById("empresa-cidade").value.trim() || null,
      estado: document.getElementById("empresa-estado").value.trim().toUpperCase() || null,
    });
    toast("Dados do estabelecimento atualizados.");
  } catch (err) {
    toast(err.message || "Voce nao possui permissao para realizar esta acao.", "danger");
  }
});

document.getElementById("form-identidade").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Api.configuracoes.atualizarEmpresa({
      tipo_estabelecimento: document.getElementById("config-tipo").value,
      cor_principal: document.getElementById("config-cor").value,
      horario_funcionamento: document.getElementById("config-horario").value.trim() || null,
    });
    toast("Identidade do estabelecimento atualizada.");
  } catch (err) {
    toast(err.message || "Voce nao possui permissao para realizar esta acao.", "danger");
  }
});

document.getElementById("form-notificacoes").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Api.preferencias.atualizarNotificacoes({
      produtos_vencendo: document.getElementById("notif-vencendo").checked,
      produtos_vencidos: document.getElementById("notif-vencidos").checked,
      estoque_baixo: document.getElementById("notif-estoque").checked,
      novas_perdas: document.getElementById("notif-perdas").checked,
      relatorios: document.getElementById("notif-relatorios").checked,
      avisos_administrativos: document.getElementById("notif-avisos").checked,
    });
    toast("Preferencias de notificacao salvas.");
  } catch (err) {
    toast(err.message || "Nao foi possivel salvar as preferencias.", "danger");
  }
});

document.getElementById("form-perfil").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const usuario = await Api.atualizarPerfil({ nome: document.getElementById("perfil-nome").value.trim() });
    Auth.setSession(Auth.getToken(), usuario);
    toast("Perfil atualizado.");
  } catch (err) {
    toast(err.message || "Nao foi possivel atualizar o perfil.", "danger");
  }
});

document.getElementById("form-senha").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Api.trocarSenha({
      senha_atual: document.getElementById("senha-atual").value,
      senha_nova: document.getElementById("senha-nova").value,
    });
    toast("Senha alterada com sucesso.");
    e.target.reset();
  } catch (err) {
    toast(err.message || "Nao foi possivel trocar a senha.", "danger");
  }
});

carregarConfig();
carregarEmpresa();
carregarNotificacoes();
carregarPerfil();
