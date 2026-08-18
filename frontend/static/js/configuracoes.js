initNav("mais");

async function carregarConfig() {
  try {
    const config = await Api.configuracoes.get();
    document.getElementById("dias-alerta-1").value = config.dias_alerta_1;
    document.getElementById("dias-alerta-2").value = config.dias_alerta_2;
    document.getElementById("dias-alerta-3").value = config.dias_alerta_3;
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

document.getElementById("form-config").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Api.configuracoes.update({
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

carregarConfig();
carregarEmpresa();
