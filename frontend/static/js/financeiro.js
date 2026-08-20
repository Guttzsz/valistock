initNav("mais");

const usuario = Auth.getUser();
if (!usuario || !usuario.super_admin) {
  toast("Voce nao tem acesso a esta area.", "danger");
  window.location.href = "dashboard.html";
}

const STATUS_LABELS = {
  trialing: "Trial",
  active: "Ativa",
  past_due: "Pagamento atrasado",
  canceled: "Cancelada",
  unpaid: "Nao pago",
  incomplete: "Incompleta",
};

const FATURA_STATUS_LABELS = {
  paga: "Paga",
  pendente: "Pendente",
  falhou: "Falhou",
  reembolsada: "Reembolsada",
};

function formatOrDados(value, formatter) {
  return value === null || value === undefined ? "Dados insuficientes" : formatter(value);
}

/* Mesma paleta categorica validada (dataviz skill) usada em relatorios.js. */
const CATEGORICAL_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
const SUCCESS_HUE = "#16a34a"; // receita: serie unica, semantica positiva (marca do ValiStock)
const INK_MUTED = "#898781";
const INK_SECONDARY = "#52514e";
const GRIDLINE = "#e1e0d9";

Chart.defaults.font.family = "'Inter', 'Segoe UI', -apple-system, sans-serif";
Chart.defaults.color = INK_SECONDARY;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.color = INK_SECONDARY;

async function carregarFinanceiro() {
  try {
    const [dashboard, receitaMensal, receitaPorPlano, assinaturas, pagamentos] = await Promise.all([
      Api.financeiro.dashboard(),
      Api.financeiro.receitaMensal(),
      Api.financeiro.receitaPorPlano(),
      Api.financeiro.assinaturas(),
      Api.financeiro.pagamentos(),
    ]);

    document.getElementById("kpi-receita-mensal").textContent = formatCurrency(dashboard.receita_mensal);
    document.getElementById("kpi-mrr").textContent = formatCurrency(dashboard.mrr);
    document.getElementById("kpi-receita-anual").textContent = formatCurrency(dashboard.receita_anual);
    document.getElementById("kpi-arr").textContent = formatCurrency(dashboard.arr);
    document.getElementById("kpi-assinaturas-ativas").textContent = dashboard.assinaturas_ativas;
    document.getElementById("kpi-clientes-pagantes").textContent = dashboard.clientes_pagantes;
    document.getElementById("kpi-trials").textContent = dashboard.trials;
    document.getElementById("kpi-cancelamentos").textContent = dashboard.cancelamentos_periodo;
    document.getElementById("kpi-inadimplencia").textContent = dashboard.inadimplencia;
    document.getElementById("kpi-arpu").textContent = formatOrDados(dashboard.arpu, formatCurrency);

    new Chart(document.getElementById("chart-receita-mensal"), {
      type: "line",
      data: {
        labels: receitaMensal.map((r) => r.mes),
        datasets: [{
          label: "Receita (R$)",
          data: receitaMensal.map((r) => r.receita),
          borderColor: SUCCESS_HUE,
          backgroundColor: "rgba(22,163,74,0.10)",
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 5,
          pointBackgroundColor: SUCCESS_HUE,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        plugins: { legend: { display: false } }, // serie unica: titulo do card ja diz o que e
        responsive: true,
        scales: {
          x: { grid: { display: false }, ticks: { color: INK_MUTED } },
          y: { grid: { color: GRIDLINE }, border: { display: false }, ticks: { color: INK_MUTED } },
        },
      },
    });

    const comClientes = receitaPorPlano.filter((p) => p.quantidade > 0);
    new Chart(document.getElementById("chart-clientes-plano"), {
      type: "doughnut",
      data: {
        labels: comClientes.map((p) => `${p.plano} (${p.quantidade})`),
        datasets: [{ data: comClientes.map((p) => p.quantidade), backgroundColor: CATEGORICAL_PALETTE, borderColor: "#fff", borderWidth: 2 }],
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } },
    });

    document.querySelector("#tabela-assinaturas tbody").innerHTML = assinaturas.length
      ? assinaturas.map((a) => `
        <tr>
          <td>${a.empresa_nome}</td>
          <td class="text-capitalize">${a.plano}</td>
          <td><span class="vs-badge ${a.status === "active" ? "normal" : a.status === "past_due" ? "urgente" : "neutro"}">${STATUS_LABELS[a.status] || a.status}</span></td>
          <td>${formatCurrency(a.valor_mensal)}</td>
          <td>${formatDate(a.periodo_atual_fim)}</td>
        </tr>
      `).join("")
      : `<tr><td colspan="5" class="text-center py-4 vs-muted">Nenhuma assinatura ainda.</td></tr>`;

    document.querySelector("#tabela-pagamentos tbody").innerHTML = pagamentos.length
      ? pagamentos.map((p) => `
        <tr>
          <td>${p.empresa_nome}</td>
          <td>${p.numero || "-"}</td>
          <td>${formatCurrency(p.valor_total)}</td>
          <td><span class="vs-badge ${p.status === "paga" ? "normal" : p.status === "falhou" ? "vencido" : "neutro"}">${FATURA_STATUS_LABELS[p.status] || p.status}</span></td>
          <td>${new Date(p.criado_em).toLocaleDateString("pt-BR")}</td>
          <td>${p.url_fatura ? `<a href="${p.url_fatura}" target="_blank" rel="noopener">Ver</a>` : ""}</td>
        </tr>
      `).join("")
      : `<tr><td colspan="6" class="text-center py-4 vs-muted">Nenhum pagamento ainda.</td></tr>`;

    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-financeiro-content").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar financeiro.", "danger");
  }
}

carregarFinanceiro();
