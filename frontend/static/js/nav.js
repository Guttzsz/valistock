/* ValiStock - topbar + bottom mobile nav, injetados em todas as paginas autenticadas. */

const NAV_ITEMS = [
  { href: "dashboard.html", icon: "\u{1F4CA}", label: "Inicio", key: "dashboard" },
  { href: "produtos.html", icon: "\u{1F4E6}", label: "Produtos", key: "produtos" },
  { href: "validades.html", icon: "⏳", label: "Validades", key: "validades" },
  { href: "alertas.html", icon: "\u{1F514}", label: "Alertas", key: "alertas" },
  { href: "mais.html", icon: "☰", label: "Mais", key: "mais" },
];

function renderTopbar() {
  const el = document.getElementById("vs-topbar");
  if (!el) return;
  const usuario = Auth.getUser();
  el.innerHTML = `
    <div class="vs-brand">
      <div class="vs-brand-mark">VS</div>
      <div>
        <div>ValiStock</div>
        <div class="vs-slogan">Menos perdas. Mais lucro.</div>
      </div>
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
  renderTopbar();
  renderBottomNav(activeKey);
}
