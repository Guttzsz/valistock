initNav("validades");

const STATUS_LABELS = {
  normal: "Normal",
  atencao: "Atencao",
  urgente: "Urgente",
  vence_hoje: "Vence hoje",
  vencido: "Vencido",
};

let statusAtual = "";

function statusBadge(status) {
  return `<span class="vs-badge ${status}">${STATUS_LABELS[status] || status}</span>`;
}

function diasLabel(dias) {
  if (dias < 0) return `${Math.abs(dias)}d atrasado`;
  if (dias === 0) return "Hoje";
  return `${dias}d`;
}

function acoesHtml(v) {
  return `
    <div class="btn-group btn-group-sm">
      <button class="btn btn-outline-success" title="Marcar como vendido" onclick="marcarVendido('${v.lote_id}')">${VsIcon("check", { size: 15 })}</button>
      <button class="btn btn-outline-danger" title="Registrar perda" onclick="irParaRegistrarPerda('${v.produto_id}','${v.lote_id}')">${VsIcon("trendingDown", { size: 15 })}</button>
      <button class="btn btn-outline-secondary" title="Criar promocao" onclick="avisoPromocaoIndisponivel()">${VsIcon("tag", { size: 15 })}</button>
    </div>
  `;
}

function renderCards(validades) {
  const el = document.getElementById("vs-validades-cards");
  if (!validades.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("checkCircle", { size: 24 })}</div>Nenhum lote encontrado para este filtro.</div>`;
    return;
  }
  el.innerHTML = validades.map((v) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${v.produto_nome}</div>
          <div class="vs-list-card-meta">${v.codigo_barras || "sem codigo"} · Lote ${v.numero_lote} · ${v.quantidade} un.</div>
        </div>
        ${statusBadge(v.status)}
      </div>
      <div class="vs-list-card-meta mb-2">Vence em ${formatDate(v.data_validade)} (${diasLabel(v.dias_restantes)}) · ${formatCurrency(v.valor_em_risco)} em risco</div>
      ${acoesHtml(v)}
    </div>
  `).join("");
}

function renderTable(validades) {
  const tbody = document.querySelector("#vs-validades-table tbody");
  if (!validades.length) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 vs-muted">Nenhum lote encontrado para este filtro.</td></tr>`;
    return;
  }
  tbody.innerHTML = validades.map((v) => `
    <tr>
      <td>${v.produto_nome}</td>
      <td>${v.codigo_barras || "-"}</td>
      <td>${v.numero_lote}</td>
      <td>${v.quantidade}</td>
      <td>${formatDate(v.data_validade)}</td>
      <td>${diasLabel(v.dias_restantes)}</td>
      <td>${formatCurrency(v.valor_em_risco)}</td>
      <td>${statusBadge(v.status)}</td>
      <td>${acoesHtml(v)}</td>
    </tr>
  `).join("");
}

async function carregarValidades() {
  try {
    const validades = await Api.validades.list(statusAtual ? { status: statusAtual } : {});
    renderCards(validades);
    renderTable(validades);
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-validades-cards").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar validades.", "danger");
  }
}

document.querySelectorAll('input[name="status"]').forEach((input) => {
  input.addEventListener("change", (e) => {
    statusAtual = e.target.value;
    carregarValidades();
  });
});

window.marcarVendido = async function (loteId) {
  try {
    await Api.lotes.marcarVendido(loteId);
    toast("Lote marcado como vendido. Estoque atualizado.");
    carregarValidades();
  } catch (err) {
    toast(err.message || "Nao foi possivel atualizar o lote.", "danger");
  }
};

window.irParaRegistrarPerda = function (produtoId, loteId) {
  window.location.href = `perdas.html?produto_id=${produtoId}&lote_id=${loteId}`;
};

window.avisoPromocaoIndisponivel = function () {
  toast("Criacao de promocoes sera adicionada em uma proxima atualizacao.", "info");
};

carregarValidades();
