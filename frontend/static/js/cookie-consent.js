/* ValiStock - banner de consentimento de cookies + preferencias, persistidas em local storage
   (mesmo mecanismo ja usado para sessao/tema). O site nao define cookies proprios hoje: usa
   local storage para sessao/aparencia, e o checkout/portal da Stripe pode definir cookies
   proprios em stripe.com. As categorias "analiticos" e "marketing" ficam disponiveis para
   travar scripts futuros (via CookieConsent.has()), mesmo nao sendo usadas nesta versao. */

const VS_COOKIE_CONSENT_KEY = "valistock_cookie_consent";
const VS_COOKIE_CONSENT_VERSION = 1;

const VS_COOKIE_CATEGORIES = [
  {
    id: "necessarios", label: "Cookies necessarios", bloqueado: true,
    desc: "Essenciais para login e navegacao segura. Nao podem ser desativados.",
  },
  {
    id: "preferencias", label: "Cookies de preferencia",
    desc: "Lembram escolhas como tema e cor de destaque nas proximas visitas.",
  },
  {
    id: "analiticos", label: "Cookies analiticos",
    desc: "Ajudariam a entender como o site e utilizado. Nao utilizados nesta versao do ValiStock.",
  },
  {
    id: "marketing", label: "Cookies de marketing",
    desc: "Usados para anuncios personalizados. Nao utilizados nesta versao do ValiStock.",
  },
];

const CookieConsent = {
  get() {
    try {
      const dados = JSON.parse(localStorage.getItem(VS_COOKIE_CONSENT_KEY));
      return dados && dados.versao === VS_COOKIE_CONSENT_VERSION ? dados : null;
    } catch (e) {
      return null;
    }
  },

  has(categoria) {
    const consentimento = this.get();
    return !!consentimento && !!consentimento[categoria];
  },

  aceitarTodos() {
    this._salvar({ preferencias: true, analiticos: true, marketing: true });
  },

  recusarOpcionais() {
    this._salvar({ preferencias: false, analiticos: false, marketing: false });
  },

  salvarPersonalizado() {
    this._salvar({
      preferencias: document.getElementById("vs-cookie-cat-preferencias").checked,
      analiticos: document.getElementById("vs-cookie-cat-analiticos").checked,
      marketing: document.getElementById("vs-cookie-cat-marketing").checked,
    });
  },

  openSettings() {
    this._ensureUI();
    const atual = this.get() || { preferencias: false, analiticos: false, marketing: false };
    document.getElementById("vs-cookie-cat-preferencias").checked = atual.preferencias;
    document.getElementById("vs-cookie-cat-analiticos").checked = atual.analiticos;
    document.getElementById("vs-cookie-cat-marketing").checked = atual.marketing;

    this._modal = this._modal || new bootstrap.Modal(document.getElementById("vs-cookie-modal"));
    this._modal.show();
  },

  init() {
    this._ensureUI();
    if (this.get()) {
      this._mostrarReabrir();
    } else {
      this._mostrarBanner();
    }
  },

  _salvar(prefs) {
    localStorage.setItem(VS_COOKIE_CONSENT_KEY, JSON.stringify({
      necessarios: true,
      preferencias: !!prefs.preferencias,
      analiticos: !!prefs.analiticos,
      marketing: !!prefs.marketing,
      versao: VS_COOKIE_CONSENT_VERSION,
      salvo_em: new Date().toISOString(),
    }));
    if (this._modal) this._modal.hide();
    this._esconderBanner();
    this._mostrarReabrir();
  },

  _mostrarBanner() {
    const banner = document.getElementById("vs-cookie-banner");
    banner.hidden = false;
    document.getElementById("vs-cookie-aceitar").focus();
  },

  _esconderBanner() {
    const banner = document.getElementById("vs-cookie-banner");
    if (!banner || banner.hidden) return;
    banner.classList.add("vs-cookie-saindo");
    banner.addEventListener("animationend", () => {
      banner.hidden = true;
      banner.classList.remove("vs-cookie-saindo");
    }, { once: true });
  },

  _mostrarReabrir() {
    const botao = document.getElementById("vs-cookie-reabrir");
    if (botao) botao.hidden = false;
  },

  _ensureUI() {
    if (document.getElementById("vs-cookie-banner")) return;
    const icone = typeof VsIcon === "function" ? VsIcon("cookie", { size: 20 }) : "";

    const categorias = VS_COOKIE_CATEGORIES.map((cat) => `
      <div class="vs-cookie-category">
        <div class="form-check form-switch">
          <input class="form-check-input" type="checkbox" id="vs-cookie-cat-${cat.id}" ${cat.bloqueado ? "checked disabled" : ""}>
          <label class="form-check-label fw-semibold" for="vs-cookie-cat-${cat.id}">${cat.label}</label>
        </div>
        <p class="small vs-muted mb-0">${cat.desc}</p>
      </div>
    `).join("");

    document.body.insertAdjacentHTML("beforeend", `
      <div class="vs-cookie-banner" id="vs-cookie-banner" role="dialog" aria-live="polite" aria-label="Aviso de cookies" hidden>
        <div class="vs-cookie-banner-inner">
          <div class="vs-cookie-banner-icon">${icone}</div>
          <div class="vs-cookie-banner-text">
            <div class="vs-cookie-banner-title">Este site utiliza cookies</div>
            <p class="vs-cookie-banner-desc">Utilizamos cookies e armazenamento local para melhorar sua experiencia, analisar o uso do site e oferecer funcionalidades personalizadas. Voce pode aceitar todos os cookies ou ajustar suas preferencias. Veja nossa <a href="cookies.html">Politica de Cookies</a>.</p>
          </div>
          <div class="vs-cookie-banner-actions">
            <button type="button" class="btn btn-outline-secondary btn-sm" id="vs-cookie-configurar">Configurar cookies</button>
            <button type="button" class="btn btn-outline-secondary btn-sm" id="vs-cookie-recusar">Recusar opcionais</button>
            <button type="button" class="btn btn-vs-primary btn-sm" id="vs-cookie-aceitar">Aceitar todos</button>
          </div>
        </div>
      </div>

      <div class="modal fade" id="vs-cookie-modal" tabindex="-1" aria-labelledby="vs-cookie-modal-titulo" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h2 class="modal-title h6 mb-0" id="vs-cookie-modal-titulo">Preferencias de cookies</h2>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
            </div>
            <div class="modal-body">
              <p class="small vs-muted">Escolha quais categorias de cookies voce permite. Veja mais detalhes na <a href="cookies.html">Politica de Cookies</a>.</p>
              ${categorias}
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-outline-secondary btn-sm" id="vs-cookie-modal-recusar">Recusar opcionais</button>
              <button type="button" class="btn btn-vs-primary btn-sm" id="vs-cookie-modal-salvar">Salvar preferencias</button>
            </div>
          </div>
        </div>
      </div>

      <button type="button" class="vs-cookie-reabrir" id="vs-cookie-reabrir" aria-label="Preferencias de cookies" title="Preferencias de cookies" hidden>${icone}</button>
    `);

    document.getElementById("vs-cookie-aceitar").addEventListener("click", () => this.aceitarTodos());
    document.getElementById("vs-cookie-recusar").addEventListener("click", () => this.recusarOpcionais());
    document.getElementById("vs-cookie-configurar").addEventListener("click", () => this.openSettings());
    document.getElementById("vs-cookie-modal-recusar").addEventListener("click", () => this.recusarOpcionais());
    document.getElementById("vs-cookie-modal-salvar").addEventListener("click", () => this.salvarPersonalizado());
    document.getElementById("vs-cookie-reabrir").addEventListener("click", () => this.openSettings());
  },
};

CookieConsent.init();
