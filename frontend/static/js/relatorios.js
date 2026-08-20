initNav("mais");

/* Paleta categorica validada (dataviz skill): ordem fixa, nunca ciclada por rank.
   node validate_palette.js confirmou: todos os checks de CVD/contraste passam
   contra a superficie #ffffff dos cards do ValiStock. */
const CATEGORICAL_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"];
const DANGER_HUE = "#dc2626"; // perdas: hue semantico unico (nao e identidade categorica, e uma unica serie negativa)

Chart.defaults.font.family = "'Inter', 'Segoe UI', -apple-system, sans-serif";

/* Cor segue a entidade, nunca a posicao no ranking (anti-padrao "recolor-on-filter"):
   trocar o filtro de periodo pode reordenar categorias por valor, mas cada nome de
   categoria mantem sempre a mesma cor depois que aparece pela primeira vez. */
const corPorCategoria = new Map();
function coresEstaveis(nomes) {
  return nomes.map((nome) => {
    if (!corPorCategoria.has(nome)) {
      corPorCategoria.set(nome, CATEGORICAL_PALETTE[corPorCategoria.size % CATEGORICAL_PALETTE.length]);
    }
    return corPorCategoria.get(nome);
  });
}

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

    const cores = VsTheme.getChartColors();
    Chart.defaults.color = cores.inkSecondary;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.color = cores.inkSecondary;

    charts.perdasDia = new Chart(document.getElementById("chart-perdas-dia"), {
      type: "line",
      data: {
        labels: perdas.perdas_por_dia.map((d) => formatDate(d.data)),
        datasets: [{
          label: "Perdas (R$)",
          data: perdas.perdas_por_dia.map((d) => d.valor),
          borderColor: DANGER_HUE,
          backgroundColor: "rgba(220,38,38,0.10)",
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 5,
          pointBackgroundColor: DANGER_HUE,
          pointBorderColor: cores.surface,
          pointBorderWidth: 2,
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        plugins: { legend: { display: false } }, // serie unica: titulo do card ja diz o que e
        responsive: true,
        scales: {
          x: { grid: { display: false }, ticks: { color: cores.inkMuted } },
          y: { grid: { color: cores.grid }, border: { display: false }, ticks: { color: cores.inkMuted } },
        },
      },
    });

    const nomesCategorias = perdas.categorias_mais_perdas.map((c) => c.categoria);
    charts.categorias = new Chart(document.getElementById("chart-categorias"), {
      type: "doughnut",
      data: {
        labels: nomesCategorias,
        datasets: [{ data: perdas.categorias_mais_perdas.map((c) => c.valor), backgroundColor: coresEstaveis(nomesCategorias), borderColor: cores.surface, borderWidth: 2 }],
      },
      options: { responsive: true, plugins: { legend: { position: "bottom" } } },
    });

    charts.produtos = new Chart(document.getElementById("chart-produtos"), {
      type: "bar",
      data: {
        labels: perdas.produtos_mais_perdas.map((p) => p.produto),
        datasets: [{
          label: "Valor perdido (R$)",
          data: perdas.produtos_mais_perdas.map((p) => p.valor),
          backgroundColor: DANGER_HUE,
          borderRadius: 4,
          maxBarThickness: 22,
        }],
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } }, // ranking de uma unica medida: cor unica = nao e identidade
        responsive: true,
        scales: {
          x: { grid: { color: cores.grid }, border: { display: false }, ticks: { color: cores.inkMuted } },
          y: { grid: { display: false }, ticks: { color: cores.inkSecondary } },
        },
      },
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
