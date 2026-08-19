initNav("mais");

function tempoRelativo(isoDatetime) {
  const data = new Date(isoDatetime);
  return data.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function render(logs) {
  const el = document.getElementById("vs-lista");
  if (!logs.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">🕓</div>Nenhuma acao registrada ainda.</div>`;
    return;
  }
  el.innerHTML = logs.map((log) => `
    <div class="vs-list-card">
      <div class="vs-list-card-title" style="font-size:0.9rem;">${log.descricao}</div>
      <div class="vs-list-card-meta">${log.usuario_nome || "Sistema"} · ${tempoRelativo(log.criado_em)}</div>
    </div>
  `).join("");
}

async function carregar() {
  document.getElementById("vs-loading").classList.remove("d-none");
  document.getElementById("vs-lista").classList.add("d-none");
  try {
    const entidade = document.getElementById("filtro-entidade").value;
    const logs = await Api.historico.list(entidade ? { entidade } : {});
    render(logs);
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-lista").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar historico.", "danger");
  }
}

document.getElementById("filtro-entidade").addEventListener("change", carregar);

carregar();
