/* ValiStock - service worker minimo, so para receber e mostrar notificacoes push.
   Sem cache offline por enquanto (fica pra quando o app for instalavel de verdade). */

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = { titulo: "ValiStock", corpo: "Voce tem um novo alerta.", url: "/templates/alertas.html" };
  try {
    if (event.data) data = { ...data, ...event.data.json() };
  } catch (e) {
    // payload nao era JSON valido, usa o texto puro como corpo
    if (event.data) data.corpo = event.data.text();
  }

  event.waitUntil(
    self.registration.showNotification(data.titulo, {
      body: data.corpo,
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/icon-192.png",
      data: { url: data.url },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/templates/alertas.html";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(url) && "focus" in client) return client.focus();
      }
      for (const client of clientList) {
        if ("focus" in client) {
          client.focus();
          return client.navigate ? client.navigate(url) : undefined;
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    })
  );
});
