initNav("mais");

const CHART_COLORS = ["#16a34a", "#eab308", "#f97316", "#dc2626", "#0f172a", "#0ea5e9", "#8b5cf6", "#ec4899"];

let charts = {};

function destroyCharts() {
  Object.values(charts).forEach((c) => c && c.destroy());
  charts = {};
}

async function carregarRelatorios() {
  const periodo = document.getElementById("filtro-periodo").value;
  document.getElementById("vs-loading").classList.remove("d-none");
  document.getElementById("vs-relatorios-content").classList.add("d-none");

  try {
    const [perdas, risco] = await Promise.all([Api.relatorios.perdas({ periodo }), Api.relatorios.risco()]);

    document.getElementById("kpi-total-perdas").textContent = formatCurrency(perdas.total_perdas);
    document.getElementById("kpi-total-risco").textContent = formatCurrency(risco.total_em_risco);

    destroyCharts();

    charts.perdasDia = new Chart(document.getElementById("chart-perdas-dia"), {
      type: "line",
      data: {
        labels: perdas.perdas_por_dia.map((d) => formatDate(d.data)),
        datasets: [{ label: "Perdas (R$)", data: perdas.perdas_por_dia.map((d) => d.valor), borderColor: CHART_COLORS[3], backgroundColor: "rgba(220,38,38,0.12)", fill: true, tension: 0.3 }],
      },
      options: { plugins: { legend: { display: false } }, responsive: true },
    });

    charts.categorias = new Chart(document.getElementById("chart-categorias"), {
      type: "doughnut",
      data: {
        labels: perdas.categorias_mais_perdas.map((c) => c.categoria),
        datasets: [{ data: perdas.categorias_mais_perdas.map((c) => c.valor), backgroundColor: CHART_COLORS }],
      },
      options: { responsive: true },
    });

    charts.produtos = new Chart(document.getElementById("chart-produtos"), {
      type: "bar",
      data: {
        labels: perdas.produtos_mais_perdas.map((p) => p.produto),
        datasets: [{ label: "Valor perdido (R$)", data: perdas.produtos_mais_perdas.map((p) => p.valor), backgroundColor: CHART_COLORS[0] }],
      },
      options: { indexAxis: "y", plugins: { legend: { display: false } }, responsive: true },
    });

    const listaRisco = document.getElementById("lista-risco");
    listaRisco.innerHTML = risco.itens.length
      ? risco.itens.slice(0, 8).map((i) => `
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
          <div>
            <div class="fw-semibold small">${i.produto}</div>
            <div class="vs-muted" style="font-size:0.78rem;">Lote ${i.lote} · vence ${formatDate(i.data_validade)}</div>
          </div>
          <span class="fw-bold text-danger">${formatCurrency(i.valor_em_risco)}</span>
        </div>
      `).join("")
      : `<div class="vs-empty py-3">Nenhum produto em risco no momento.</div>`;

    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-relatorios-content").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar relatorios.", "danger");
  }
}

document.getElementById("filtro-periodo").addEventListener("change", carregarRelatorios);

document.getElementById("btn-exportar-csv").addEventListener("click", async () => {
  const periodo = document.getElementById("filtro-periodo").value;
  try {
    await Api.relatorios.exportarPerdasCsv({ periodo });
  } catch (err) {
    toast(err.message || "Nao foi possivel exportar o relatorio.", "danger");
  }
});

carregarRelatorios();
