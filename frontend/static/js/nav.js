/* ValiStock - topbar + nav desktop + bottom mobile nav, injetados em todas as paginas autenticadas. */

const NAV_ITEMS = [
  { href: "dashboard.html", icon: "\u{1F4CA}", label: "Inicio", key: "dashboard" },
  { href: "produtos.html", icon: "\u{1F4E6}", label: "Produtos", key: "produtos" },
  { href: "validades.html", icon: "⏳", label: "Validades", key: "validades" },
  { href: "alertas.html", icon: "\u{1F514}", label: "Alertas", key: "alertas" },
  { href: "mais.html", icon: "☰", label: "Mais", key: "mais" },
];

/* Itens que na versao mobile ficam dentro de "Mais", mas no desktop aparecem
   num dropdown na barra superior (senao ficam inacessiveis em telas largas). */
const MAIS_ITEMS = [
  { href: "perdas.html", label: "📉 Controle de Perdas", key: "perdas" },
  { href: "relatorios.html", label: "📊 Relatorios", key: "relatorios" },
  { href: "categorias.html", label: "🏷 Categorias", key: "categorias" },
  { href: "fornecedores.html", label: "🚚 Fornecedores", key: "fornecedores" },
  { href: "localizacoes.html", label: "📍 Locais da loja", key: "localizacoes" },
  { href: "usuarios.html", label: "👥 Usuarios", key: "usuarios" },
  { href: "historico.html", label: "🕓 Historico", key: "historico" },
  { href: "planos.html", label: "💳 Plano e assinatura", key: "planos" },
  { href: "configuracoes.html", label: "⚙️ Configuracoes", key: "configuracoes" },
];

function itensMais(usuario) {
  return usuario?.super_admin ? [...MAIS_ITEMS, { href: "financeiro.html", label: "💼 Financeiro (plataforma)", key: "financeiro" }] : MAIS_ITEMS;
}

function renderTopbar(activeKey) {
  const el = document.getElementById("vs-topbar");
  if (!el) return;
  const usuario = Auth.getUser();
  const itens = itensMais(usuario);

  const linksDesktop = NAV_ITEMS.slice(0, 4).map((item) => `
    <a href="${item.href}" class="vs-desktop-link ${item.key === activeKey ? "active" : ""}">${item.icon} ${item.label}</a>
  `).join("");

  const maisAtivo = itens.some((i) => i.key === activeKey) || activeKey === "mais";

  el.innerHTML = `
    <div class="vs-topbar-left">
      <div class="vs-brand">
        <div class="vs-brand-mark">VS</div>
        <div>
          <div>ValiStock</div>
          <div class="vs-slogan">Menos perdas. Mais lucro.</div>
        </div>
      </div>
      <nav class="vs-desktop-nav d-none d-lg-flex">
        ${linksDesktop}
        <div class="dropdown">
          <a href="#" class="vs-desktop-link ${maisAtivo ? "active" : ""}" data-bs-toggle="dropdown" aria-expanded="false">☰ Mais</a>
          <ul class="dropdown-menu">
            ${itens.map((item) => `<li><a class="dropdown-item" href="${item.href}">${item.label}</a></li>`).join("")}
          </ul>
        </div>
      </nav>
    </div>
    <div class="dropdown">
      <button class="btn btn-sm btn-light border rounded-circle" style="width:38px;height:38px;" data-bs-toggle="dropdown" aria-expanded="false">
        ${(usuario?.nome || "?").charAt(0).toUpperCase()}
      </button>
      <ul class="dropdown-menu dropdown-menu-end">
        <li><span class="dropdown-item-text small text-muted">${usuario?.nome || ""}<br>${usuario?.email || ""}</span></li>
        <li><hr class="dropdown-divider"></li>
        <li><a class="dropdown-item" href="configuracoes.html">Configuracoes</a></li>
        <li><a class="dropdown-item text-danger" href="#" id="vs-logout-link">Sair</a></li>
      </ul>
    </div>
  `;
  document.getElementById("vs-logout-link")?.addEventListener("click", (e) => {
    e.preventDefault();
    Auth.logout();
  });
}

function renderBottomNav(activeKey) {
  const el = document.getElementById("vs-bottom-nav");
  if (!el) return;
  el.className = "vs-bottom-nav";
  el.innerHTML = NAV_ITEMS.map((item) => `
    <a href="${item.href}" class="vs-nav-item ${item.key === activeKey ? "active" : ""}">
      <span class="vs-nav-icon ${item.key === "alertas" ? "vs-nav-badge" : ""}" ${item.key === "alertas" ? 'id="vs-nav-alert-count" data-count="0"' : ""}>${item.icon}</span>
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

function initNav(activeKey) {
  Auth.requireAuth();
  renderTopbar(activeKey);
  renderBottomNav(activeKey);
}
