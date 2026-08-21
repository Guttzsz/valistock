/* ValiStock - notificacoes push (Web Push). Registra o service worker em toda
   pagina autenticada (via initNav) mas so pede permissao quando o usuario clica
   em "ativar" - navegadores penalizam pedir permissao sem interacao. */

function _vsUrlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

const VsPush = {
  suportado() {
    return "serviceWorker" in navigator && "PushManager" in window;
  },

  async init() {
    if (!this.suportado()) return null;
    try {
      return await navigator.serviceWorker.register("/service-worker.js");
    } catch (e) {
      return null;
    }
  },

  async status() {
    if (!this.suportado()) return "indisponivel";
    if (Notification.permission === "denied") return "negado";
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) return "inativo";
    const sub = await registration.pushManager.getSubscription();
    return sub ? "ativo" : "inativo";
  },

  async ativar() {
    if (!this.suportado()) throw new Error("Este navegador nao suporta notificacoes.");

    const permissao = await Notification.requestPermission();
    if (permissao !== "granted") throw new Error("Permissao de notificacao negada.");

    const registration = (await navigator.serviceWorker.getRegistration()) || (await this.init());
    const { chave } = await Api.push.chavePublica();
    if (!chave) throw new Error("Notificacoes push nao estao configuradas neste ambiente.");

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: _vsUrlBase64ToUint8Array(chave),
    });

    await Api.push.inscrever(subscription.toJSON());
    return true;
  },

  async desativar() {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) return;
    const sub = await registration.pushManager.getSubscription();
    if (!sub) return;
    await Api.push.desinscrever({ endpoint: sub.endpoint });
    await sub.unsubscribe();
  },
};

if (typeof Auth !== "undefined" && Auth.isAuthenticated()) {
  VsPush.init();
}
