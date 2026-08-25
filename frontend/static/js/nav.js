/* ValiStock - topbar + nav desktop + bottom mobile nav, injetados em todas as paginas autenticadas. */

function renderAparenciaRapida() {
  const { theme, accent } = VsTheme.get();
  const temas = [
    { valor: "dia", icon: "sun", titulo: "Dia" },
    { valor: "noite", icon: "moon", titulo: "Noite" },
    { valor: "automatico", icon: "monitor", titulo: "Automatico" },
  ];
  return `
    <li class="px-2 py-2">
      <div class="small fw-semibold vs-muted mb-2 px-1">Aparencia</div>
      <div class="d-flex gap-1 mb-2" id="vs-quick-theme">
        ${temas.map((t) => `
          <button type="button" class="btn btn-sm btn-outline-secondary flex-fill vs-theme-opt ${t.valor === theme ? "active" : ""}" data-theme-opt="${t.valor}" title="${t.titulo}">${VsIcon(t.icon, { size: 14 })}</button>
        `).join("")}
      </div>
      <div class="d-flex flex-wrap gap-2 px-1" id="vs-quick-accent">
        ${Object.entries(VS_ACCENT_HEX).map(([nome, hex]) => `
          <button type="button" class="vs-accent-dot ${nome === accent ? "active" : ""}" data-accent-opt="${nome}" style="background:${hex}" title="${nome}"></button>
        `).join("")}
      </div>
    </li>
    <li><hr class="dropdown-divider"></li>
  `;
}

function ligarAparenciaRapida(container) {
  container.querySelectorAll(".vs-theme-opt").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const { accent } = VsTheme.get();
      await VsTheme.set(btn.dataset.themeOpt, accent);
      container.querySelectorAll(".vs-theme-opt").forEach((b) => b.classList.toggle("active", b === btn));
    });
  });
  container.querySelectorAll(".vs-accent-dot").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const { theme } = VsTheme.get();
      await VsTheme.set(theme, btn.dataset.accentOpt);
      container.querySelectorAll(".vs-accent-dot").forEach((b) => b.classList.toggle("active", b === btn));
    });
  });
}

const NAV_ITEMS = [
  { href: "dashboard.html", icon: "home", label: "Inicio", key: "dashboard" },
  { href: "produtos.html", icon: "box", label: "Produtos", key: "produtos" },
  { href: "validades.html", icon: "clock", label: "Validades", key: "validades" },
  { href: "alertas.html", icon: "bell", label: "Alertas", key: "alertas" },
  { href: "mais.html", icon: "menu", label: "Mais", key: "mais" },
];

/* Itens que na versao mobile ficam dentro de "Mais", mas no desktop aparecem
   num dropdown na barra superior (senao ficam inacessiveis em telas largas). */
const MAIS_ITEMS = [
  { href: "perdas.html", icon: "trendingDown", label: "Controle de Perdas", key: "perdas" },
  { href: "relatorios.html", icon: "barChart", label: "Relatorios", key: "relatorios" },
  { href: "categorias.html", icon: "tag", label: "Categorias", key: "categorias" },
  { href: "fornecedores.html", icon: "truck", label: "Fornecedores", key: "fornecedores" },
  { href: "localizacoes.html", icon: "mapPin", label: "Locais da loja", key: "localizacoes" },
  { href: "usuarios.html", icon: "users", label: "Usuarios", key: "usuarios" },
  { href: "historico.html", icon: "history", label: "Historico", key: "historico" },
  { href: "planos.html", icon: "creditCard", label: "Plano e assinatura", key: "planos" },
  { href: "configuracoes.html", icon: "settings", label: "Configuracoes", key: "configuracoes" },
];

function itensMais(usuario) {
  return usuario?.super_admin
    ? [...MAIS_ITEMS, { href: "financeiro.html", icon: "briefcase", label: "Financeiro (plataforma)", key: "financeiro" }]
    : MAIS_ITEMS;
}

function renderTopbar(activeKey) {
  const el = document.getElementById("vs-topbar");
  if (!el) return;
  const usuario = Auth.getUser();
  const itens = itensMais(usuario);

  const linksDesktop = NAV_ITEMS.slice(0, 4).map((item) => `
    <a href="${item.href}" class="vs-desktop-link ${item.key === activeKey ? "active" : ""}">${VsIcon(item.icon, { size: 16 })} ${item.label}</a>
  `).join("");

  const maisAtivo = itens.some((i) => i.key === activeKey) || activeKey === "mais";

  el.innerHTML = `
    <div class="vs-topbar-left">
      <div class="vs-brand">
        <div class="vs-brand-mark">${VS_BRAND_MARK_SVG}</div>
        <div>
          <div>ValiStock</div>
          <div class="vs-slogan">Menos perdas. Mais lucro.</div>
        </div>
      </div>
      <nav class="vs-desktop-nav d-none d-lg-flex">
        ${linksDesktop}
        <div class="dropdown">
          <a href="#" class="vs-desktop-link ${maisAtivo ? "active" : ""}" data-bs-toggle="dropdown" aria-expanded="false">${VsIcon("menu", { size: 16 })} Mais</a>
          <ul class="dropdown-menu">
            ${itens.map((item) => `<li><a class="dropdown-item d-flex align-items-center gap-2" href="${item.href}">${VsIcon(item.icon, { size: 16, class: "vs-muted" })} ${item.label}</a></li>`).join("")}
          </ul>
        </div>
      </nav>
    </div>
    <div class="dropdown">
      <button class="vs-avatar-btn" data-bs-toggle="dropdown" aria-expanded="false">
        ${(usuario?.nome || "?").charAt(0).toUpperCase()}
      </button>
      <ul class="dropdown-menu dropdown-menu-end" data-bs-auto-close="outside">
        <li><span class="dropdown-item-text small text-muted">${usuario?.nome || ""}<br>${usuario?.email || ""}</span></li>
        <li><hr class="dropdown-divider"></li>
        ${renderAparenciaRapida()}
        <li><a class="dropdown-item d-flex align-items-center gap-2" href="configuracoes.html">${VsIcon("settings", { size: 16, class: "vs-muted" })} Configuracoes</a></li>
        <li><a class="dropdown-item d-flex align-items-center gap-2 text-danger" href="#" id="vs-logout-link">${VsIcon("logOut", { size: 16 })} Sair</a></li>
      </ul>
    </div>
  `;
  document.getElementById("vs-logout-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    Auth.logout();
  });
  ligarAparenciaRapida(el);
}

function renderBottomNav(activeKey) {
  const el = document.getElementById("vs-bottom-nav");
  if (!el) return;
  el.className = "vs-bottom-nav";
  el.innerHTML = NAV_ITEMS.map((item) => `
    <a href="${item.href}" class="vs-nav-item ${item.key === activeKey ? "active" : ""}">
      <span class="vs-nav-icon ${item.key === "alertas" ? "vs-nav-badge" : ""}" ${item.key === "alertas" ? 'id="vs-nav-alert-count" data-count="0"' : ""}>${VsIcon(item.icon, { size: 22 })}</span>
      <span>${item.label}</span>
    </a>
  `).join("");

  if (Auth.isAuthenticated()) {
    Api.alertas.list({ lido: false }).then((alertas) => {
      const badge = document.getElementById("vs-nav-alert-count");
      if (badge) badge.setAttribute("data-count", String(alertas.length));
    }).catch(() => {});
  }
}

function _vsCarregarPush() {
  if (document.getElementById("vs-manifest-link")) return;
  const link = document.createElement("link");
  link.id = "vs-manifest-link";
  link.rel = "manifest";
  link.href = "/manifest.json";
  document.head.appendChild(link);

  const script = document.createElement("script");
  script.src = "/static/js/push.js";
  script.onload = () => document.dispatchEvent(new Event("vs:push-ready"));
  document.body.appendChild(script);
}

function initNav(activeKey) {
  Auth.requireAuth();
  renderTopbar(activeKey);
  renderBottomNav(activeKey);
  if (typeof VsApplyIcons === "function") VsApplyIcons();
  if (typeof VsWirePasswordToggles === "function") VsWirePasswordToggles();
  _vsCarregarPush();
}
