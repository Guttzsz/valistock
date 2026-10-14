// ValiStock para Windows: uma janela nativa que abre o ValiStock online.
// O conteudo vem sempre de valistock.vercel.app, entao toda atualizacao publicada no site
// chega ao app de PC na hora, sem precisar gerar um instalador novo.
const { app, BrowserWindow, shell, Menu } = require("electron");
const path = require("path");

const APP_URL = "https://valistock.vercel.app/templates/dashboard.html";
const APP_HOST = "valistock.vercel.app";
// O checkout e o portal de assinatura do Stripe abrem dentro do app e voltam para o ValiStock.
const HOSTS_PERMITIDOS = new Set([APP_HOST, "checkout.stripe.com", "billing.stripe.com"]);

let janela = null;

function hostPermitido(url) {
  try {
    const u = new URL(url);
    return u.protocol === "https:" && HOSTS_PERMITIDOS.has(u.hostname);
  } catch {
    return false;
  }
}

function criarJanela() {
  janela = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 380,
    minHeight: 600,
    title: "ValiStock",
    icon: path.join(__dirname, "build", "icon.png"),
    backgroundColor: "#f4f6f9",
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  janela.once("ready-to-show", () => janela.show());
  janela.loadURL(APP_URL);

  // Links para fora do ValiStock/Stripe (e-mail, sites externos) abrem no navegador padrao.
  janela.webContents.setWindowOpenHandler(({ url }) => {
    if (hostPermitido(url)) return { action: "allow" };
    if (/^(https?|mailto):/.test(url)) shell.openExternal(url);
    return { action: "deny" };
  });
  janela.webContents.on("will-navigate", (event, url) => {
    if (!hostPermitido(url)) {
      event.preventDefault();
      if (/^(https?|mailto):/.test(url)) shell.openExternal(url);
    }
  });

  // Sem internet: mostra a tela local, que tenta de novo.
  janela.webContents.on("did-fail-load", (_event, codigo, _desc, _url, principal) => {
    if (principal && codigo !== -3) janela.loadFile(path.join(__dirname, "offline.html"));
  });
}

// Uma unica instancia: abrir o atalho de novo so traz a janela para frente.
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (!janela) return;
    if (janela.isMinimized()) janela.restore();
    janela.focus();
  });

  app.setAppUserModelId("com.valistock.app");
  Menu.setApplicationMenu(null);
  app.whenReady().then(criarJanela);
  app.on("window-all-closed", () => app.quit());
}
