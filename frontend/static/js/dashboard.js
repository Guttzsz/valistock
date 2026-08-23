initNav("dashboard");

const STATUS_LABELS = {
  normal: "Normal",
  atencao: "Atencao",
  urgente: "Urgente",
  vence_hoje: "Vence hoje",
  vencido: "Vencido",
};

function statusBadge(status) {
  return `<span class="vs-badge ${status}">${STATUS_LABELS[status] || status}</span>`;
}

const VS_PROMO_DISMISS_KEY = "valistock_promo_planos_fechado";

async function configurarPromoPlanos() {
  const card = document.getElementById("vs-promo-planos");
  if (localStorage.getItem(VS_PROMO_DISMISS_KEY) === "1") return;

  try {
    const sub = await Api.subscription.atual();
    if (sub.plano !== "gratuito") return; // quem ja paga nao precisa ver incentivo pra assinar
  } catch (err) {
    return; // sem info de plano, nao mostra (evita incentivar quem ja pode ser assinante)
  }

  card.classList.remove("d-none");

  document.getElementById("vs-promo-fechar").addEventListener("click", () => {
    card.classList.add("vs-promo-saindo");
    localStorage.setItem(VS_PROMO_DISMISS_KEY, "1");
    card.addEventListener("animationend", () => card.classList.add("d-none"), { once: true });
  });
}

async function loadDashboard() {
  const usuario = Auth.getUser();
  document.getElementById("vs-greeting").textContent = usuario ? `Ola, ${usuario.nome.split(" ")[0]}!` : "Ola!";

  try {
    const [dashboard, validades, alertas] = await Promise.all([
      Api.dashboard(),
      Api.validades.list(),
      Api.alertas.list({ lido: false }),
    ]);

    document.getElementById("kpi-produtos").textContent = dashboard.produtos_cadastrados;
    document.getElementById("kpi-proximos").textContent = dashboard.lotes_proximos_vencimento;
    document.getElementById("kpi-vencidos").textContent = dashboard.lotes_vencidos;
    document.getElementById("kpi-valor-risco").textContent = formatCurrency(dashboard.valor_em_risco);
    document.getElementById("kpi-perdas-mes").textContent = formatCurrency(dashboard.perdas_do_mes);
    document.getElementById("kpi-economia").textContent = formatCurrency(dashboard.economia_potencial);

    const urgentes = validades
      .filter((v) => ["urgente", "vence_hoje", "vencido"].includes(v.status))
      .slice(0, 5);

    const urgentesList = document.getElementById("vs-urgentes-list");
    urgentesList.innerHTML = urgentes.length
      ? urgentes.map((v) => `
        <div class="vs-list-card">
          <div class="vs-list-card-top">
            <div class="vs-list-card-title">${v.produto_nome}</div>
            ${statusBadge(v.status)}
          </div>
          <div class="vs-list-card-meta">Lote ${v.numero_lote} · ${v.quantidade} un. · vence em ${formatDate(v.data_validade)} · ${formatCurrency(v.valor_em_risco)} em risco</div>
        </div>
      `).join("")
      : `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("checkCircle", { size: 24 })}</div>Nenhum produto urgente no momento.</div>`;

    const alertasList = document.getElementById("vs-alertas-list");
    alertasList.innerHTML = alertas.length
      ? alertas.slice(0, 5).map((a) => `
        <div class="vs-list-card">
          <div class="vs-list-card-title">${a.mensagem}</div>
          <div class="vs-list-card-meta">${formatDate(a.data_alerta)}</div>
        </div>
      `).join("")
      : `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("bell", { size: 24 })}</div>Voce esta em dia com os alertas.</div>`;

    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-dashboard-content").classList.remove("d-none");

    configurarPromoPlanos();
  } catch (err) {
    toast(err.message || "Erro ao carregar dashboard.", "danger");
  }
}

loadDashboard();
