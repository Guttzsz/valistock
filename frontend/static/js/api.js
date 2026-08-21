/* ValiStock - cliente da API.
   API_BASE_URL pode ser sobrescrito antes deste script carregar via:
   <script>window.VALISTOCK_API_BASE_URL = "https://api.seudominio.com";</script>
*/
const API_BASE_URL = window.VALISTOCK_API_BASE_URL || "http://localhost:8000";

const TOKEN_KEY = "valistock_token";
const USER_KEY = "valistock_user";

const Auth = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setSession(token, usuario) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(usuario));
  },
  clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  isAuthenticated() {
    return !!this.getToken();
  },
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = "login.html";
    }
  },
  logout() {
    this.clearSession();
    window.location.href = "login.html";
  },
};

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function apiRequest(path, { method = "GET", body, params, auth = true } = {}) {
  let url = `${API_BASE_URL}${path}`;
  if (params) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") query.append(key, value);
    });
    const qs = query.toString();
    if (qs) url += `?${qs}`;
  }

  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (networkError) {
    throw new ApiError("Nao foi possivel conectar ao servidor. Verifique sua internet.", 0);
  }

  if (response.status === 401 && auth) {
    Auth.clearSession();
    window.location.href = "login.html";
    throw new ApiError("Sessao expirada.", 401);
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    const message = (data && data.detail) || "Ocorreu um erro. Tente novamente.";
    throw new ApiError(message, response.status);
  }

  return data;
}

const Api = {
  register: (payload) => apiRequest("/api/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiRequest("/api/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest("/api/auth/me"),
  permissoes: () => apiRequest("/api/auth/permissoes"),
  atualizarPerfil: (payload) => apiRequest("/api/auth/perfil", { method: "PUT", body: payload }),
  trocarSenha: (payload) => apiRequest("/api/auth/senha", { method: "PUT", body: payload }),
  atualizarAparencia: (payload) => apiRequest("/api/auth/aparencia", { method: "PUT", body: payload }),

  dashboard: () => apiRequest("/api/dashboard"),

  produtos: {
    list: (params) => apiRequest("/api/produtos", { params }),
    get: (id) => apiRequest(`/api/produtos/${id}`),
    create: (payload) => apiRequest("/api/produtos", { method: "POST", body: payload }),
    update: (id, payload) => apiRequest(`/api/produtos/${id}`, { method: "PUT", body: payload }),
    remove: (id) => apiRequest(`/api/produtos/${id}`, { method: "DELETE" }),
    porCodigoBarras: (codigo) => apiRequest(`/api/produtos/buscar/codigo-barras/${encodeURIComponent(codigo)}`),
  },

  lotes: {
    list: (params) => apiRequest("/api/lotes", { params }),
    create: (payload) => apiRequest("/api/lotes", { method: "POST", body: payload }),
    update: (id, payload) => apiRequest(`/api/lotes/${id}`, { method: "PUT", body: payload }),
    remove: (id) => apiRequest(`/api/lotes/${id}`, { method: "DELETE" }),
    marcarVendido: (id) => apiRequest(`/api/lotes/${id}/marcar-vendido`, { method: "PUT" }),
  },

  validades: {
    list: (params) => apiRequest("/api/validades", { params }),
  },

  alertas: {
    list: (params) => apiRequest("/api/alertas", { params }),
    marcarLido: (id) => apiRequest(`/api/alertas/${id}/ler`, { method: "PUT" }),
    ignorar: (id) => apiRequest(`/api/alertas/${id}/ignorar`, { method: "PUT" }),
  },

  perdas: {
    list: (params) => apiRequest("/api/perdas", { params }),
    create: (payload) => apiRequest("/api/perdas", { method: "POST", body: payload }),
  },

  relatorios: {
    perdas: (params) => apiRequest("/api/relatorios/perdas", { params }),
    risco: () => apiRequest("/api/relatorios/risco"),
    exportarPerdasCsv: async (params) => {
      const query = new URLSearchParams(params || {}).toString();
      const response = await fetch(`${API_BASE_URL}/api/relatorios/perdas/exportar${query ? `?${query}` : ""}`, {
        headers: { Authorization: `Bearer ${Auth.getToken()}` },
      });
      if (!response.ok) throw new ApiError("Nao foi possivel exportar o relatorio.", response.status);
      const blob = await response.blob();
      const nome = (response.headers.get("Content-Disposition") || "").match(/filename="(.+)"/)?.[1] || "perdas.csv";
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = nome;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    },
  },

  usuarios: {
    list: () => apiRequest("/api/usuarios"),
    create: (payload) => apiRequest("/api/usuarios", { method: "POST", body: payload }),
    update: (id, payload) => apiRequest(`/api/usuarios/${id}`, { method: "PUT", body: payload }),
    remove: (id) => apiRequest(`/api/usuarios/${id}`, { method: "DELETE" }),
  },

  configuracoes: {
    get: () => apiRequest("/api/configuracoes"),
    atualizarAlertas: (payload) => apiRequest("/api/configuracoes/alertas", { method: "PUT", body: payload }),
    atualizarEmpresa: (payload) => apiRequest("/api/configuracoes/empresa", { method: "PUT", body: payload }),
    atualizarOnboarding: (payload) => apiRequest("/api/configuracoes/onboarding", { method: "PUT", body: payload }),
  },

  empresa: {
    get: () => apiRequest("/api/empresas/atual"),
    update: (payload) => apiRequest("/api/empresas/atual", { method: "PUT", body: payload }),
  },

  subscription: {
    atual: () => apiRequest("/api/subscriptions/atual"),
    faturas: () => apiRequest("/api/subscriptions/faturas"),
    checkout: (plano) => apiRequest("/api/subscriptions/checkout", { method: "POST", body: { plano } }),
    portal: () => apiRequest("/api/subscriptions/portal", { method: "POST" }),
  },

  financeiro: {
    dashboard: () => apiRequest("/api/financeiro/dashboard"),
    receitaMensal: () => apiRequest("/api/financeiro/receita-mensal"),
    receitaPorPlano: () => apiRequest("/api/financeiro/receita-por-plano"),
    assinaturas: () => apiRequest("/api/financeiro/assinaturas"),
    pagamentos: () => apiRequest("/api/financeiro/pagamentos"),
    sincronizar: (empresaId) => apiRequest(`/api/financeiro/sincronizar/${empresaId}`, { method: "POST" }),
  },

  categorias: {
    list: (params) => apiRequest("/api/categorias", { params }),
    create: (payload) => apiRequest("/api/categorias", { method: "POST", body: payload }),
    update: (id, payload) => apiRequest(`/api/categorias/${id}`, { method: "PUT", body: payload }),
    remove: (id) => apiRequest(`/api/categorias/${id}`, { method: "DELETE" }),
  },

  fornecedores: {
    list: (params) => apiRequest("/api/fornecedores", { params }),
    create: (payload) => apiRequest("/api/fornecedores", { method: "POST", body: payload }),
    update: (id, payload) => apiRequest(`/api/fornecedores/${id}`, { method: "PUT", body: payload }),
    remove: (id) => apiRequest(`/api/fornecedores/${id}`, { method: "DELETE" }),
  },

  localizacoes: {
    list: (params) => apiRequest("/api/localizacoes", { params }),
    create: (payload) => apiRequest("/api/localizacoes", { method: "POST", body: payload }),
    update: (id, payload) => apiRequest(`/api/localizacoes/${id}`, { method: "PUT", body: payload }),
    remove: (id) => apiRequest(`/api/localizacoes/${id}`, { method: "DELETE" }),
  },

  camposPersonalizados: {
    list: () => apiRequest("/api/campos-personalizados"),
    create: (payload) => apiRequest("/api/campos-personalizados", { method: "POST", body: payload }),
    remove: (id) => apiRequest(`/api/campos-personalizados/${id}`, { method: "DELETE" }),
    valoresDoProduto: (produtoId) => apiRequest(`/api/produtos/${produtoId}/campos-personalizados`),
    definirValoresDoProduto: (produtoId, payload) =>
      apiRequest(`/api/produtos/${produtoId}/campos-personalizados`, { method: "PUT", body: payload }),
  },

  historico: {
    list: (params) => apiRequest("/api/historico", { params }),
    estoque: (params) => apiRequest("/api/historico/estoque", { params }),
  },

  preferencias: {
    getNotificacoes: () => apiRequest("/api/preferencias/notificacoes"),
    atualizarNotificacoes: (payload) => apiRequest("/api/preferencias/notificacoes", { method: "PUT", body: payload }),
    getDashboard: () => apiRequest("/api/preferencias/dashboard"),
    atualizarDashboard: (payload) => apiRequest("/api/preferencias/dashboard", { method: "PUT", body: payload }),
  },

  push: {
    chavePublica: () => apiRequest("/api/push/chave-publica"),
    inscrever: (payload) => apiRequest("/api/push/inscrever", { method: "POST", body: payload }),
    desinscrever: (payload) => apiRequest("/api/push/inscrever", { method: "DELETE", body: payload }),
  },
};

function formatCurrency(value) {
  const n = Number(value) || 0;
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(isoDate) {
  if (!isoDate) return "-";
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

function toast(message, variant = "success") {
  const container = document.getElementById("vs-toast-container") || (() => {
    const el = document.createElement("div");
    el.id = "vs-toast-container";
    el.style.cssText = "position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:1080;width:min(92vw,380px);";
    document.body.appendChild(el);
    return el;
  })();

  const icons = { success: "checkCircle", danger: "xCircle", info: "alertTriangle" };
  const iconHtml = typeof VsIcon === "function" ? VsIcon(icons[variant] || icons.info, { size: 16 }) : "";
  const toastEl = document.createElement("div");
  toastEl.className = `vs-toast ${variant}`;
  toastEl.innerHTML = `${iconHtml}<span>${message}</span>`;
  container.appendChild(toastEl);
  setTimeout(() => toastEl.remove(), 3500);
}
