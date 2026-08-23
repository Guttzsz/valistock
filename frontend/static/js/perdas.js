initNav("mais");

const MOTIVO_LABELS = {
  produto_vencido: "Produto vencido",
  produto_danificado: "Produto danificado",
  armazenamento_inadequado: "Armazenamento inadequado",
  erro_de_estoque: "Erro de estoque",
  outro: "Outro",
};

let produtosCache = [];
let lotesCache = [];

function periodoParaDatas(valor) {
  if (!valor) return {};
  const hoje = new Date();
  const fim = hoje.toISOString().slice(0, 10);
  if (valor === "hoje") return { data_inicio: fim, data_fim: fim };
  const dias = Number(valor);
  const inicio = new Date(hoje);
  inicio.setDate(inicio.getDate() - dias);
  return { data_inicio: inicio.toISOString().slice(0, 10), data_fim: fim };
}

function renderPerdas(perdas) {
  const el = document.getElementById("vs-perdas-list");
  const tbody = document.querySelector("#vs-perdas-table tbody");
  if (!perdas.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("trendingDown", { size: 24 })}</div>Nenhuma perda registrada neste periodo.</div>`;
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 vs-muted">Nenhuma perda registrada neste periodo.</td></tr>`;
    document.getElementById("total-periodo").textContent = formatCurrency(0);
    return;
  }

  const total = perdas.reduce((acc, p) => acc + Number(p.valor_total), 0);
  document.getElementById("total-periodo").textContent = formatCurrency(total);

  el.innerHTML = perdas.map((p) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${p.produto_nome}</div>
          <div class="vs-list-card-meta">${MOTIVO_LABELS[p.motivo] || p.motivo} · ${formatDate(p.data_perda)} · ${p.usuario_nome || "-"}</div>
        </div>
        <span class="vs-badge vencido">${formatCurrency(p.valor_total)}</span>
      </div>
      <div class="vs-list-card-meta">${p.quantidade} un. × ${formatCurrency(p.valor_unitario)}${p.observacao ? " · " + p.observacao : ""}</div>
    </div>
  `).join("");

  tbody.innerHTML = perdas.map((p) => `
    <tr>
      <td>${p.produto_nome}</td>
      <td>${MOTIVO_LABELS[p.motivo] || p.motivo}</td>
      <td>${formatDate(p.data_perda)}</td>
      <td>${p.usuario_nome || "-"}</td>
      <td>${p.quantidade}</td>
      <td>${formatCurrency(p.valor_unitario)}</td>
      <td><span class="vs-badge vencido">${formatCurrency(p.valor_total)}</span></td>
    </tr>
  `).join("");
}

async function carregarPerdas() {
  const periodo = document.getElementById("filtro-periodo").value;
  const motivo = document.getElementById("filtro-motivo").value;
  const params = { ...periodoParaDatas(periodo), motivo: motivo || undefined };

  try {
    const perdas = await Api.perdas.list(params);
    renderPerdas(perdas);
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-perdas-list").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar perdas.", "danger");
  }
}

document.getElementById("filtro-periodo").addEventListener("change", carregarPerdas);
document.getElementById("filtro-motivo").addEventListener("change", carregarPerdas);

// ---------- Modal: registrar perda ----------
const modalPerda = new bootstrap.Modal(document.getElementById("modal-perda"));
const formPerda = document.getElementById("form-perda");
const selectProduto = document.getElementById("perda-produto");
const selectLote = document.getElementById("perda-lote");

async function popularProdutos() {
  produtosCache = await Api.produtos.list();
  selectProduto.innerHTML = produtosCache.map((p) => `<option value="${p.id}">${p.nome}</option>`).join("");
}

async function popularLotes(produtoId) {
  lotesCache = produtoId ? await Api.lotes.list({ produto_id: produtoId }) : [];
  selectLote.innerHTML = `<option value="">Sem lote especifico</option>` + lotesCache
    .filter((l) => l.quantidade > 0)
    .map((l) => `<option value="${l.id}">${l.numero_lote} (${l.quantidade} un., vence ${formatDate(l.data_validade)})</option>`)
    .join("");
}

selectProduto.addEventListener("change", () => popularLotes(selectProduto.value));

formPerda.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    produto_id: selectProduto.value,
    lote_id: selectLote.value || null,
    quantidade: Number(document.getElementById("perda-quantidade").value),
    motivo: document.getElementById("perda-motivo").value,
    observacao: document.getElementById("perda-observacao").value.trim() || null,
  };
  try {
    await Api.perdas.create(payload);
    toast("Perda registrada com sucesso.");
    modalPerda.hide();
    formPerda.reset();
    carregarPerdas();
  } catch (err) {
    toast(err.message || "Nao foi possivel registrar a perda.", "danger");
  }
});

async function preencherViaQueryString() {
  const params = new URLSearchParams(window.location.search);
  const produtoId = params.get("produto_id");
  const loteId = params.get("lote_id");
  if (produtoId) {
    await popularLotes(produtoId);
    selectProduto.value = produtoId;
    if (loteId) selectLote.value = loteId;
    modalPerda.show();
  }
}

(async function init() {
  await popularProdutos();
  await carregarPerdas();
  await preencherViaQueryString();
})();
