Auth.requireAuth();
if (typeof VsApplyIcons === "function") VsApplyIcons();
if (typeof VsApplyBrandMarks === "function") VsApplyBrandMarks();

const CATEGORIAS_SUGERIDAS = ["Laticinios", "Bebidas", "Hortifruti", "Carnes", "Padaria", "Congelados", "Higiene", "Limpeza"];
const TOTAL_ETAPAS = 9;

const estado = {
  etapa: 2,
  tipo_estabelecimento: null,
  quantidade_funcionarios_aprox: null,
  quantidade_produtos_aprox: null,
  categorias_selecionadas: new Set(),
};

function mostrarEtapa(numero) {
  document.querySelectorAll(".onboarding-step").forEach((el) => el.classList.add("d-none"));
  const el = document.getElementById(`step-${numero}`);
  if (el) el.classList.remove("d-none");
  document.getElementById("progress-bar").style.width = `${Math.round((numero / TOTAL_ETAPAS) * 100)}%`;
}

async function salvarEtapa(payload) {
  try {
    await Api.configuracoes.atualizarOnboarding(payload);
  } catch (err) {
    toast(err.message || "Erro ao salvar. Suas respostas podem nao ter sido guardadas.", "danger");
  }
}

// Etapa 2: tipo de estabelecimento
document.querySelectorAll("#tipo-options button").forEach((btn) => {
  btn.addEventListener("click", async () => {
    estado.tipo_estabelecimento = btn.dataset.tipo;
    estado.etapa = 3;
    await salvarEtapa({ etapa: 3, tipo_estabelecimento: estado.tipo_estabelecimento });
    mostrarEtapa(3);
  });
});
document.getElementById("btn-tipo-outro").addEventListener("click", () => {
  const input = document.getElementById("tipo-outro");
  if (input.classList.contains("d-none")) {
    input.classList.remove("d-none");
    input.focus();
    return;
  }
  const valor = input.value.trim();
  if (!valor) return;
  salvarEtapa({ etapa: 3, tipo_estabelecimento: "outro", tipo_estabelecimento_outro: valor }).then(() => mostrarEtapa(3));
});

// Etapa 3: funcionarios
document.querySelectorAll("#func-options button").forEach((btn) => {
  btn.addEventListener("click", async () => {
    estado.quantidade_funcionarios_aprox = btn.dataset.valor;
    await salvarEtapa({ etapa: 4, quantidade_funcionarios_aprox: btn.dataset.valor });
    mostrarEtapa(4);
  });
});

// Etapa 4: produtos
document.querySelectorAll("#produtos-options button").forEach((btn) => {
  btn.addEventListener("click", async () => {
    estado.quantidade_produtos_aprox = btn.dataset.valor;
    await salvarEtapa({ etapa: 5, quantidade_produtos_aprox: btn.dataset.valor });
    renderCategorias();
    mostrarEtapa(5);
  });
});

// Etapa 5: categorias
function renderCategorias() {
  const container = document.getElementById("categorias-options");
  container.innerHTML = CATEGORIAS_SUGERIDAS.map((c) => `
    <button type="button" class="btn btn-sm btn-outline-secondary rounded-pill categoria-toggle" data-nome="${c}">${c}</button>
  `).join("");
  container.querySelectorAll(".categoria-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const nome = btn.dataset.nome;
      if (estado.categorias_selecionadas.has(nome)) {
        estado.categorias_selecionadas.delete(nome);
        btn.classList.remove("btn-vs-primary");
        btn.classList.add("btn-outline-secondary");
      } else {
        estado.categorias_selecionadas.add(nome);
        btn.classList.remove("btn-outline-secondary");
        btn.classList.add("btn-vs-primary");
      }
    });
  });
}

document.getElementById("step-5-continuar").addEventListener("click", async () => {
  const extra = document.getElementById("categoria-extra").value.trim();
  if (extra) estado.categorias_selecionadas.add(extra);
  await salvarEtapa({ etapa: 6, categorias_iniciais: [...estado.categorias_selecionadas] });
  mostrarEtapa(6);
});

// Etapa 6: alertas
document.getElementById("step-6-continuar").addEventListener("click", async () => {
  await salvarEtapa({
    etapa: 7,
    dias_alerta_1: Number(document.getElementById("alerta-1").value) || 7,
    dias_alerta_2: Number(document.getElementById("alerta-2").value) || 3,
    dias_alerta_3: Number(document.getElementById("alerta-3").value) || 1,
  });
  mostrarEtapa(7);
});

// Etapa 7: notificacoes
document.getElementById("step-7-continuar").addEventListener("click", async () => {
  try {
    await Api.preferencias.atualizarNotificacoes({
      produtos_vencendo: document.getElementById("notif-vencendo").checked,
      produtos_vencidos: true,
      estoque_baixo: document.getElementById("notif-estoque").checked,
      novas_perdas: document.getElementById("notif-perdas").checked,
      relatorios: false,
      avisos_administrativos: true,
    });
  } catch (err) {
    // nao bloqueia o fluxo se as preferencias falharem ao salvar
  }
  await salvarEtapa({ etapa: 8 });
  mostrarEtapa(8);
});

// Etapa 8: aparencia
function renderCoresAparencia() {
  const container = document.getElementById("aparencia-cor-options");
  const { accent } = VsTheme.get();
  container.innerHTML = Object.entries(VS_ACCENT_HEX).map(([nome, hex]) => `
    <button type="button" class="vs-accent-dot ${nome === accent ? "active" : ""}" data-accent-opt="${nome}" style="background:${hex}" title="${nome}"></button>
  `).join("");
  container.querySelectorAll(".vs-accent-dot").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const { theme } = VsTheme.get();
      await VsTheme.set(theme, btn.dataset.accentOpt);
      container.querySelectorAll(".vs-accent-dot").forEach((b) => b.classList.toggle("active", b === btn));
    });
  });
}
renderCoresAparencia();

document.querySelectorAll("#aparencia-tema-options .vs-theme-opt").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const { accent } = VsTheme.get();
    await VsTheme.set(btn.dataset.themeOpt, accent);
    document.querySelectorAll("#aparencia-tema-options .vs-theme-opt").forEach((b) => b.classList.toggle("active", b === btn));
  });
});

document.getElementById("step-8-continuar").addEventListener("click", async () => {
  await salvarEtapa({ etapa: 9 });
  mostrarEtapa(9);
});

// Etapa 9: conclusao
document.getElementById("btn-concluir").addEventListener("click", async () => {
  await salvarEtapa({ etapa: 9, concluir: true });
  window.location.href = "dashboard.html";
});

mostrarEtapa(estado.etapa);
