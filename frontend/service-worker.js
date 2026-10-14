/* ValiStock - service worker: deixa o app instalavel (PC e celular), mostra uma tela
   offline quando nao ha internet e recebe as notificacoes push.
   Estrategia "rede primeiro": com internet, tudo vem sempre atualizado do servidor; o cache
   so e usado como reserva offline. A API (outro dominio) nunca passa pelo cache. */

const CACHE = "valistock-v1";
const OFFLINE_URL = "/offline.html";
const PRECACHE = [
  OFFLINE_URL,
  "/manifest.json",
  "/static/css/style.css",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((nomes) => Promise.all(nomes.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;

  event.respondWith(
    fetch(req)
      .then((resp) => {
        if (resp.ok) {
          const copia = resp.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copia));
        }
        return resp;
      })
      .catch(async () => {
        const emCache = await caches.match(req, { ignoreSearch: req.mode === "navigate" });
        if (emCache) return emCache;
        if (req.mode === "navigate") return caches.match(OFFLINE_URL);
        return Response.error();
      })
  );
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
