/* ValiStock - controlador de tema/cor de destaque.
   Carregado logo apos o <link rel="stylesheet"> e antes de qualquer outro script,
   para aplicar o tema salvo antes do primeiro paint (evita flash de tema errado). */
const VS_THEME_KEY = "valistock_theme";
const VS_ACCENT_KEY = "valistock_accent";
const VS_THEMES = ["dia", "noite", "automatico"];
const VS_ACCENTS = ["azul", "verde", "roxo", "laranja", "vermelho", "ciano", "rosa", "amarelo"];
const VS_ACCENT_HEX = {
  azul: "#2563eb", verde: "#15803d", roxo: "#7c3aed", laranja: "#ea580c",
  vermelho: "#dc2626", ciano: "#0891b2", rosa: "#db2777", amarelo: "#ca8a04",
};

const VsTheme = {
  get() {
    const theme = localStorage.getItem(VS_THEME_KEY);
    const accent = localStorage.getItem(VS_ACCENT_KEY);
    return {
      theme: VS_THEMES.includes(theme) ? theme : "automatico",
      accent: VS_ACCENTS.includes(accent) ? accent : "azul",
    };
  },

  _resolvido(theme) {
    if (theme !== "automatico") return theme;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "noite" : "dia";
  },

  _aplicarNoDom(theme, accent) {
    const resolvido = this._resolvido(theme);
    const modo = resolvido === "noite" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", modo);
    document.documentElement.setAttribute("data-accent", accent);
    // Tambem liga o dark mode nativo do Bootstrap (data-bs-theme), para que
    // qualquer classe utilitaria pura do Bootstrap (.text-muted, .btn-close, table
    // striping etc.) que ainda nao foi migrada para os tokens --vs-* va junto.
    document.documentElement.setAttribute("data-bs-theme", modo);
  },

  init() {
    const { theme, accent } = this.get();
    this._aplicarNoDom(theme, accent);

    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        const atual = this.get();
        if (atual.theme === "automatico") this._aplicarNoDom(atual.theme, atual.accent);
      });
    }
  },

  /** Aplica no DOM, grava local (cache) e persiste no backend (fonte da verdade) se logado. */
  async set(theme, accent) {
    localStorage.setItem(VS_THEME_KEY, theme);
    localStorage.setItem(VS_ACCENT_KEY, accent);
    this._aplicarNoDom(theme, accent);

    if (typeof Auth !== "undefined" && Auth.isAuthenticated()) {
      try {
        const usuario = await Api.atualizarAparencia({ theme, accent_color: accent });
        Auth.setSession(Auth.getToken(), usuario);
      } catch (err) {
        // Nao bloqueia a troca visual se a persistencia falhar (ex.: offline); o
        // localStorage ja garante que a escolha sobrevive a um F5.
      }
    }
  },

  /** Aplica a partir do objeto de usuario retornado pelo login/registro (fonte de verdade = banco). */
  sincronizarComUsuario(usuario) {
    if (!usuario) return;
    if (VS_THEMES.includes(usuario.theme)) localStorage.setItem(VS_THEME_KEY, usuario.theme);
    if (VS_ACCENTS.includes(usuario.accent_color)) localStorage.setItem(VS_ACCENT_KEY, usuario.accent_color);
    const { theme, accent } = this.get();
    this._aplicarNoDom(theme, accent);
  },

  /** Cores de tinta/grade atuais, para os graficos Chart.js (canvas nao enxerga CSS custom properties). */
  getChartColors() {
    const cs = getComputedStyle(document.documentElement);
    const v = (name) => cs.getPropertyValue(name).trim();
    return {
      ink: v("--vs-dark"),
      inkSecondary: v("--vs-slate"),
      inkMuted: v("--vs-slate-light"),
      grid: v("--vs-border"),
      surface: v("--vs-card"),
    };
  },
};

VsTheme.init();

(function vsInjetarFavicon() {
  const link = document.createElement("link");
  link.rel = "icon";
  link.type = "image/png";
  link.href = "/static/icons/favicon-32.png";
  document.head.appendChild(link);
})();
