/* ValiStock - app instalavel (PWA). Carregado em todas as paginas: registra o service worker
   e controla os botoes "Instalar app" (qualquer elemento com data-vs-install).
   - Chrome/Edge (PC e Android): usa o prompt nativo de instalacao do navegador.
   - iPhone/iPad e Safari do Mac: nao existe prompt nativo, entao mostra o passo a passo.
   - Ja instalado (abrindo como app) ou navegador sem suporte: os botoes ficam escondidos. */

const VsInstall = {
  _prompt: null,

  instalado() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  },

  plataforma() {
    const ua = navigator.userAgent;
    const ios = /iphone|ipad|ipod/i.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
    if (ios) return "ios";
    const safariMac = /Macintosh/.test(ua) && /Safari/.test(ua) && !/Chrome|Chromium|Edg|Firefox/.test(ua);
    if (safariMac) return "safari-mac";
    return "outro";
  },

  disponivel() {
    if (this.instalado()) return false;
    return Boolean(this._prompt) || ["ios", "safari-mac"].includes(this.plataforma());
  },

  async instalar() {
    if (this._prompt) {
      const prompt = this._prompt;
      this._prompt = null;
      prompt.prompt();
      await prompt.userChoice.catch(() => null);
      this.atualizarBotoes();
      return;
    }
    this._mostrarInstrucoes(this.plataforma());
  },

  atualizarBotoes() {
    const mostrar = this.disponivel();
    document.querySelectorAll("[data-vs-install]").forEach((el) => el.classList.toggle("d-none", !mostrar));
  },

  _mostrarInstrucoes(plataforma) {
    document.getElementById("vs-install-sheet")?.remove();
    const passos = plataforma === "safari-mac"
      ? [
          "No Safari, abra o menu <strong>Arquivo</strong> na barra do topo.",
          "Clique em <strong>Adicionar ao Dock</strong>.",
          "Confirme em <strong>Adicionar</strong>. O ValiStock aparece no Dock e no Launchpad.",
        ]
      : [
          "Toque no botao <strong>Compartilhar</strong> do Safari (o quadrado com a seta para cima).",
          "Role e toque em <strong>Adicionar a Tela de Inicio</strong>.",
          "Toque em <strong>Adicionar</strong>. O ValiStock aparece na sua tela como um app.",
        ];
    const aviso = plataforma === "ios"
      ? '<p class="vs-install-sheet-note">Use o <strong>Safari</strong>: em outros navegadores do iPhone a opcao pode nao aparecer.</p>'
      : "";

    const el = document.createElement("div");
    el.id = "vs-install-sheet";
    el.className = "vs-install-sheet";
    el.innerHTML = `
      <div class="vs-install-sheet-card" role="dialog" aria-modal="true" aria-labelledby="vs-install-titulo">
        <div class="vs-install-sheet-head">
          <img src="/static/icons/icon-192.png" alt="" width="44" height="44">
          <div>
            <div id="vs-install-titulo" class="vs-install-sheet-title">Instalar o ValiStock</div>
            <div class="vs-install-sheet-sub">Abra direto da tela inicial, em tela cheia, como um app.</div>
          </div>
        </div>
        <ol class="vs-install-sheet-steps">${passos.map((p) => `<li>${p}</li>`).join("")}</ol>
        ${aviso}
        <button type="button" class="btn btn-vs-primary w-100" data-vs-install-fechar>Entendi</button>
      </div>`;
    el.addEventListener("click", (e) => {
      if (e.target === el || e.target.closest("[data-vs-install-fechar]")) el.remove();
    });
    document.body.appendChild(el);
  },
};

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault(); // guarda o prompt para disparar so quando o usuario clicar em "Instalar app"
  VsInstall._prompt = e;
  VsInstall.atualizarBotoes();
});

window.addEventListener("appinstalled", () => {
  VsInstall._prompt = null;
  VsInstall.atualizarBotoes();
});

document.addEventListener("click", (e) => {
  if (e.target.closest("[data-vs-install]")) {
    e.preventDefault();
    VsInstall.instalar();
  }
});

// Botoes podem ser criados depois (ex.: topbar montada pelo nav.js), entao reavalia apos o carregamento.
document.addEventListener("DOMContentLoaded", () => VsInstall.atualizarBotoes());
window.addEventListener("load", () => VsInstall.atualizarBotoes());

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}
