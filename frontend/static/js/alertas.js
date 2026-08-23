initNav("alertas");

const TIPO_LABELS = {
  vencimento_7_dias: { label: "7 dias", cls: "atencao" },
  vencimento_3_dias: { label: "3 dias", cls: "urgente" },
  vencimento_1_dia: { label: "1 dia", cls: "urgente" },
  vence_hoje: { label: "Vence hoje", cls: "vence_hoje" },
  vencido: { label: "Vencido", cls: "vencido" },
  estoque_baixo: { label: "Estoque baixo", cls: "estoque_baixo" },
};

let filtroAtual = "nao-lidos";

function acoesAlertaHtml(a) {
  return `
    ${!a.lido ? `<button class="btn btn-sm btn-outline-secondary" onclick="marcarLido('${a.id}')">Marcar como lido</button>` : ""}
    <button class="btn btn-sm btn-outline-danger" onclick="ignorarAlerta('${a.id}')">Ignorar</button>
    <a class="btn btn-sm btn-outline-secondary" href="perdas.html?produto_id=${a.produto_id}">Registrar perda</a>
    <button class="btn btn-sm btn-outline-secondary" onclick="avisoPromocaoIndisponivel()">Criar promocao</button>
  `;
}

function renderAlertas(alertas) {
  const el = document.getElementById("vs-alertas-list");
  const tbody = document.querySelector("#vs-alertas-table tbody");
  if (!alertas.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("bell", { size: 24 })}</div>Nenhum alerta por aqui.</div>`;
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 vs-muted">Nenhum alerta por aqui.</td></tr>`;
    return;
  }
  el.innerHTML = alertas.map((a) => {
    const tipo = TIPO_LABELS[a.tipo] || { label: a.tipo, cls: "neutro" };
    return `
      <div class="vs-list-card ${a.lido ? "opacity-75" : ""}">
        <div class="vs-list-card-top">
          <div>
            <div class="vs-list-card-title">${a.mensagem}</div>
            <div class="vs-list-card-meta">${a.produto_nome} · ${formatDate(a.data_alerta)}</div>
          </div>
          <span class="vs-badge ${tipo.cls}">${tipo.label}</span>
        </div>
        <div class="d-flex gap-2 flex-wrap mt-2">${acoesAlertaHtml(a)}</div>
      </div>
    `;
  }).join("");

  tbody.innerHTML = alertas.map((a) => {
    const tipo = TIPO_LABELS[a.tipo] || { label: a.tipo, cls: "neutro" };
    return `
      <tr class="${a.lido ? "opacity-75" : ""}">
        <td>${a.mensagem}</td>
        <td>${a.produto_nome}</td>
        <td>${formatDate(a.data_alerta)}</td>
        <td><span class="vs-badge ${tipo.cls}">${tipo.label}</span></td>
        <td><div class="d-flex gap-2 flex-wrap">${acoesAlertaHtml(a)}</div></td>
      </tr>
    `;
  }).join("");
}

async function carregarAlertas() {
  document.getElementById("vs-loading").classList.remove("d-none");
  document.getElementById("vs-alertas-list").classList.add("d-none");

  const params = {};
  if (filtroAtual === "nao-lidos") params.lido = false;
  if (filtroAtual === "lidos") params.lido = true;

  try {
    const alertas = await Api.alertas.list(params);
    renderAlertas(alertas);
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-alertas-list").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar alertas.", "danger");
  }
}

document.querySelectorAll("#tabs-alertas .nav-link").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#tabs-alertas .nav-link").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    filtroAtual = btn.dataset.filter;
    carregarAlertas();
  });
});

window.marcarLido = async function (id) {
  try {
    await Api.alertas.marcarLido(id);
    toast("Alerta marcado como lido.");
    carregarAlertas();
  } catch (err) {
    toast(err.message || "Nao foi possivel atualizar o alerta.", "danger");
  }
};

window.ignorarAlerta = async function (id) {
  try {
    await Api.alertas.ignorar(id);
    toast("Alerta ignorado.");
    carregarAlertas();
  } catch (err) {
    toast(err.message || "Nao foi possivel ignorar o alerta.", "danger");
  }
};

window.avisoPromocaoIndisponivel = function () {
  toast("Criacao de promocoes sera adicionada em uma proxima atualizacao.", "info");
};

async function atualizarBannerPush() {
  if (typeof VsPush === "undefined" || !VsPush.suportado()) return;
  const status = await VsPush.status();
  document.getElementById("vs-push-banner").classList.toggle("d-none", status !== "inativo");
}

document.getElementById("btn-ativar-push").addEventListener("click", async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  btn.classList.add("is-loading");
  try {
    await VsPush.ativar();
    toast("Notificacoes ativadas neste aparelho.");
    document.getElementById("vs-push-banner").classList.add("d-none");
  } catch (err) {
    toast(err.message || "Nao foi possivel ativar as notificacoes.", "danger");
  } finally {
    btn.disabled = false;
    btn.classList.remove("is-loading");
  }
});

if (typeof VsPush !== "undefined") {
  atualizarBannerPush();
} else {
  document.addEventListener("vs:push-ready", atualizarBannerPush, { once: true });
}

carregarAlertas();
