/* ValiStock - conjunto de icones SVG inline (estilo stroke, 24x24), sem dependencia externa.
   Uso: VsIcon("box") retorna uma string HTML de <svg>. Puramente apresentacional. */

/* Marca do ValiStock: calendario + check. Sempre injetada dentro de .vs-brand-mark, que ja
   fornece o fundo em gradiente (reage a cor de destaque escolhida pelo usuario). O check usa
   var(--vs-primary-700) para acompanhar essa mesma cor automaticamente. */
const VS_BRAND_MARK_SVG =
  '<svg width="65%" height="65%" viewBox="0 0 100 100" aria-hidden="true">' +
  '<rect x="34" y="18" width="7" height="16" rx="3.5" fill="white"/>' +
  '<rect x="59" y="18" width="7" height="16" rx="3.5" fill="white"/>' +
  '<rect x="22" y="30" width="56" height="48" rx="10" fill="white"/>' +
  '<path d="M32 54 L44 66 L70 40" stroke="var(--vs-primary-700)" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' +
  '</svg>';

const VS_ICON_PATHS = {
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9 21v-6h6v6"/>',
  box: '<path d="M21 8 12 3 3 8v8l9 5 9-5Z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 21a2 2 0 0 0 4 0"/>',
  menu: '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
  trendingDown: '<path d="M3 7l7 7 4-4 7 7"/><path d="M15 21h6v-6"/>',
  trendingUp: '<path d="M3 17l7-7 4 4 7-7"/><path d="M15 3h6v6"/>',
  barChart: '<path d="M4 20V10"/><path d="M12 20V4"/><path d="M20 20v-7"/>',
  tag: '<path d="M12.6 2.7 21 11.1a2 2 0 0 1 0 2.8l-7.1 7.1a2 2 0 0 1-2.8 0L2.7 12.6a2 2 0 0 1-.6-1.4V4a1.3 1.3 0 0 1 1.3-1.3h7.2c.5 0 1 .2 1.4.6Z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
  truck: '<rect x="1" y="6" width="14" height="11" rx="1.5"/><path d="M15 10h4l3 3v4h-7z"/><circle cx="6" cy="19" r="1.7"/><circle cx="17.5" cy="19" r="1.7"/>',
  mapPin: '<path d="M20 10.5c0 6-8 11.5-8 11.5S4 16.5 4 10.5a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10.5" r="2.7"/>',
  users: '<circle cx="9" cy="8" r="3.3"/><path d="M2.5 20c0-3.5 3-6.2 6.5-6.2s6.5 2.7 6.5 6.2"/><path d="M16.2 5a3.3 3.3 0 0 1 0 6.4"/><path d="M17.5 13.8c2.6.5 4 2.5 4 6.2"/>',
  history: '<circle cx="12" cy="12" r="9"/><path d="M3.5 8.5H8V4"/><path d="M12 7v5l3.5 2"/>',
  creditCard: '<rect x="2.5" y="5.5" width="19" height="13" rx="2"/><path d="M2.5 10h19"/><path d="M6 15h4"/>',
  briefcase: '<rect x="2.5" y="7.5" width="19" height="12" rx="2"/><path d="M8 7.5V5.8A1.8 1.8 0 0 1 9.8 4h4.4A1.8 1.8 0 0 1 16 5.8V7.5"/><path d="M2.5 13h19"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.6V3a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.6 1H21a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.4 1Z"/>',
  logOut: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
  dollar: '<circle cx="12" cy="12" r="9"/><path d="M12 6.5v11"/><path d="M15.5 9.3a3 3 0 0 0-3-1.8c-1.9 0-3.2 1-3.2 2.4 0 3 6.2 1.4 6.2 4.4 0 1.5-1.4 2.5-3.2 2.5a3.4 3.4 0 0 1-3.3-1.9"/>',
  xCircle: '<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/>',
  checkCircle: '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
  alertTriangle: '<path d="M10.3 3.9 2 18a1.8 1.8 0 0 0 1.6 2.7h16.8A1.8 1.8 0 0 0 22 18L13.7 3.9a1.8 1.8 0 0 0-3.4 0Z"/><path d="M12 9.3v4.2"/><path d="M12 16.8h.01"/>',
  camera: '<path d="M4 8h3l1.5-2.3h7L17 8h3a1.5 1.5 0 0 1 1.5 1.5V19a1.5 1.5 0 0 1-1.5 1.5H4A1.5 1.5 0 0 1 2.5 19V9.5A1.5 1.5 0 0 1 4 8Z"/><circle cx="12" cy="14" r="3.6"/>',
  check: '<path d="M20 6.5 9 17.5l-5-5"/>',
  search: '<circle cx="11" cy="11" r="7.2"/><path d="M21 21l-4.5-4.5"/>',
  plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
  boxPackage: '<path d="M21 8 12 3 3 8v8l9 5 9-5Z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/><path d="M16.5 5.5 7.5 10.5"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-2.6-6.3"/><path d="M21 4v5h-5"/>',
  inbox: '<path d="M4 12h4l2 3h4l2-3h4"/><path d="M5.5 5h13l2.5 7v7a1.5 1.5 0 0 1-1.5 1.5H4A1.5 1.5 0 0 1 2.5 19v-7Z"/>',
  chevronRight: '<path d="M9 6l6 6-6 6"/>',
  chevronLeft: '<path d="M15 6l-6 6 6 6"/>',
  download: '<path d="M12 3v13"/><path d="M7 11l5 5 5-5"/><path d="M4 20h16"/>',
  sun: '<circle cx="12" cy="12" r="4.3"/><path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7"/>',
  moon: '<path d="M20.5 14.7A8.5 8.5 0 1 1 9.3 3.5a7 7 0 0 0 11.2 11.2Z"/>',
  monitor: '<rect x="2.5" y="4" width="19" height="13" rx="1.8"/><path d="M8 20.5h8M12 17v3.5"/>',
  palette: '<path d="M12 2.5a9.5 9.5 0 1 0 0 19c1.1 0 2-.9 2-2 0-.5-.2-.9-.5-1.3-.3-.3-.5-.8-.5-1.2 0-1.1.9-2 2-2H17a4.5 4.5 0 0 0 4.5-4.5C21.5 6.5 17.2 2.5 12 2.5Z"/><circle cx="7.2" cy="12" r="1.15"/><circle cx="8.6" cy="7.8" r="1.15"/><circle cx="13" cy="6.5" r="1.15"/><circle cx="17" cy="9" r="1.15"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="M3 3l18 18"/><path d="M10.6 5.2A10.6 10.6 0 0 1 12 5c6.5 0 10 7 10 7a15.7 15.7 0 0 1-3.4 4.3M6.6 6.6C3.9 8.3 2 12 2 12s3.5 7 10 7c1.4 0 2.7-.3 3.8-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
  cookie: '<path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"/><path d="M8.5 8.5v.01"/><path d="M16 15.5v.01"/><path d="M12 12v.01"/><path d="M11 17v.01"/><path d="M7 14v.01"/>',
  mail: '<rect x="2.5" y="4.5" width="19" height="15" rx="2.2"/><path d="M3 6.2l9 6.1 9-6.1"/>',
  lock: '<rect x="4" y="11" width="16" height="10" rx="2.2"/><path d="M8 11V7.3a4 4 0 0 1 8 0V11"/>',
};

function VsIcon(name, opts) {
  const paths = VS_ICON_PATHS[name];
  if (!paths) return "";
  const cls = (opts && opts.class) || "";
  const size = (opts && opts.size) || 20;
  return `<svg xmlns="http://www.w3.org/2000/svg" class="${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
}

/* Aplica icones em qualquer elemento estatico marcado com data-vs-icon="nome",
   sem precisar reescrever o HTML de cada pagina em JS. Chamado automaticamente
   por initNav() em toda pagina autenticada. */
function VsApplyIcons(root) {
  (root || document).querySelectorAll("[data-vs-icon]:not([data-vs-icon-applied])").forEach((el) => {
    const size = Number(el.getAttribute("data-vs-icon-size")) || 18;
    el.insertAdjacentHTML("afterbegin", VsIcon(el.getAttribute("data-vs-icon"), { size }));
    el.setAttribute("data-vs-icon-applied", "1");
  });
}

/* Injeta a marca do ValiStock em todo .vs-brand-mark estatico (login/cadastro/onboarding).
   O topbar (montado via JS em nav.js) ja recebe o SVG direto no template, sem precisar disso. */
function VsApplyBrandMarks(root) {
  (root || document).querySelectorAll(".vs-brand-mark:not([data-vs-brandmark-applied])").forEach((el) => {
    el.innerHTML = VS_BRAND_MARK_SVG;
    el.setAttribute("data-vs-brandmark-applied", "1");
  });
}

/* Envolve todo <input type="password"> com um botao de mostrar/ocultar senha,
   sem precisar editar cada formulario (login, cadastro, configuracoes, usuarios...). */
function VsWirePasswordToggles(root) {
  (root || document).querySelectorAll('input[type="password"]:not([data-vs-pw-wired])').forEach((input) => {
    input.setAttribute("data-vs-pw-wired", "1");

    const wrap = document.createElement("div");
    wrap.className = "vs-password-wrap";
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "vs-password-toggle";
    btn.setAttribute("aria-label", "Mostrar senha");
    btn.setAttribute("aria-pressed", "false");
    btn.innerHTML = VsIcon("eye", { size: 18 });
    wrap.appendChild(btn);

    btn.addEventListener("click", () => {
      const mostrando = input.type === "text";
      input.type = mostrando ? "password" : "text";
      btn.setAttribute("aria-pressed", String(!mostrando));
      btn.setAttribute("aria-label", mostrando ? "Mostrar senha" : "Ocultar senha");
      btn.innerHTML = VsIcon(mostrando ? "eye" : "eyeOff", { size: 18 });
    });
  });
}
