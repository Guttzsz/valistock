initNav("produtos");

let produtosCache = [];
let categoriasCache = [];
let fornecedoresCache = [];
let localizacoesCache = [];

function acoesProdutoHtml(p) {
  return `
    <button class="btn btn-sm btn-outline-secondary" onclick="abrirEdicaoProduto('${p.id}')">Editar</button>
    <button class="btn btn-sm btn-vs-primary" onclick="abrirNovoLote('${p.id}', '${p.nome.replace(/'/g, "\\'")}')">+ Lote</button>
    <button class="btn btn-sm btn-outline-danger" onclick="removerProduto('${p.id}', '${p.nome.replace(/'/g, "\\'")}')">Excluir</button>
  `;
}

function renderProdutos(produtos) {
  const container = document.getElementById("vs-produtos-list");
  const tbody = document.querySelector("#vs-produtos-table tbody");
  if (!produtos.length) {
    container.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("box", { size: 24 })}</div>Nenhum produto encontrado.<br><span class="small">Cadastre seu primeiro produto para comecar.</span></div>`;
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-4 vs-muted">Nenhum produto encontrado.</td></tr>`;
    return;
  }

  container.innerHTML = produtos.map((p) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${p.nome}</div>
          <div class="vs-list-card-meta">${p.codigo_barras || "sem codigo"} · ${p.categoria_nome || "sem categoria"}${p.localizacao_nome ? ` · ${p.localizacao_nome}` : ""}</div>
        </div>
        <span class="vs-badge ${p.estoque_atual <= p.estoque_minimo ? "urgente" : "normal"}">${p.estoque_atual} ${p.unidade_medida}</span>
      </div>
      <div class="vs-list-card-meta mb-2">Custo ${formatCurrency(p.preco_custo)} · Venda ${formatCurrency(p.preco_venda)}${p.fornecedor_nome ? ` · ${p.fornecedor_nome}` : ""}</div>
      <div class="d-flex gap-2 flex-wrap">${acoesProdutoHtml(p)}</div>
    </div>
  `).join("");

  tbody.innerHTML = produtos.map((p) => `
    <tr>
      <td>${p.nome}</td>
      <td>${p.codigo_barras || "-"}</td>
      <td>${p.categoria_nome || "-"}</td>
      <td>${p.localizacao_nome || "-"}</td>
      <td><span class="vs-badge ${p.estoque_atual <= p.estoque_minimo ? "urgente" : "normal"}">${p.estoque_atual} ${p.unidade_medida}</span></td>
      <td>${formatCurrency(p.preco_custo)}</td>
      <td>${formatCurrency(p.preco_venda)}</td>
      <td>${p.fornecedor_nome || "-"}</td>
      <td><div class="d-flex gap-2 flex-wrap">${acoesProdutoHtml(p)}</div></td>
    </tr>
  `).join("");
}

function popularSelect(select, itens, valorAtual, placeholder) {
  const atual = valorAtual !== undefined ? valorAtual : select.value;
  select.innerHTML = `<option value="">${placeholder}</option>` + itens.map((i) => `<option value="${i.id}">${i.nome}</option>`).join("");
  select.value = atual || "";
}

/* Mesma coisa que popularSelect, mas com uma opcao extra no fim pra cadastrar um item novo
   sem sair do formulario de produto (usado pelos selects de fornecedor e localizacao). */
function popularSelectComNovo(select, itens, valorAtual, placeholder, rotuloNovo) {
  popularSelect(select, itens, valorAtual, placeholder);
  const opt = document.createElement("option");
  opt.value = "__novo__";
  opt.textContent = rotuloNovo;
  select.appendChild(opt);
}

/* Liga um select a um fluxo de "cadastrar novo": ao escolher a opcao __novo__, pede o nome,
   cria via API e ja deixa o item recem-criado selecionado.
   getCache/setCache leem e gravam a variavel de cache correta (fornecedoresCache/localizacoesCache) -
   nao da pra so guardar o array numa closure porque carregarListasAuxiliares() substitui esse array
   inteiro (nao muta), entao uma referencia capturada de antemao ficaria presa na lista vazia inicial. */
function ligarCriacaoRapida(select, { getCache, setCache, apiCriar, placeholder, rotuloNovo, pergunta }) {
  select.addEventListener("change", async () => {
    if (select.value !== "__novo__") return;
    const nome = (prompt(pergunta) || "").trim();
    if (!nome) {
      select.value = "";
      return;
    }
    try {
      const novo = await apiCriar({ nome });
      setCache([...getCache(), novo]);
      popularSelectComNovo(select, getCache(), novo.id, placeholder, rotuloNovo);
      toast(`"${novo.nome}" cadastrado.`);
    } catch (err) {
      select.value = "";
      toast(err.message || "Nao foi possivel cadastrar.", "danger");
    }
  });
}

function popularFiltroCategorias() {
  const select = document.getElementById("filtro-categoria");
  const atual = select.value;
  select.innerHTML = `<option value="">Todas categorias</option>` + categoriasCache.map((c) => `<option value="${c.id}">${c.nome}</option>`).join("");
  select.value = atual;
}

async function carregarListasAuxiliares() {
  try {
    [categoriasCache, fornecedoresCache, localizacoesCache] = await Promise.all([
      Api.categorias.list(),
      Api.fornecedores.list(),
      Api.localizacoes.list(),
    ]);
    popularFiltroCategorias();
    popularSelectComNovo(document.getElementById("produto-categoria"), categoriasCache, "", "Sem categoria", "+ Nova categoria...");
    popularSelectComNovo(document.getElementById("produto-fornecedor"), fornecedoresCache, "", "Sem fornecedor", "+ Novo fornecedor...");
    popularSelectComNovo(document.getElementById("produto-localizacao"), localizacoesCache, "", "Sem localizacao", "+ Novo local...");
  } catch (err) {
    toast(err.message || "Erro ao carregar categorias/fornecedores.", "danger");
  }
}

async function carregarProdutos() {
  try {
    produtosCache = await Api.produtos.list();
    aplicarFiltros();
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-produtos-list").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar produtos.", "danger");
  }
}

function aplicarFiltros() {
  const termo = document.getElementById("busca").value.trim().toLowerCase();
  const categoriaId = document.getElementById("filtro-categoria").value;
  const filtrados = produtosCache.filter((p) => {
    const bateTermo = !termo || p.nome.toLowerCase().includes(termo) || (p.codigo_barras || "").includes(termo);
    const bateCategoria = !categoriaId || p.categoria_id === categoriaId;
    return bateTermo && bateCategoria;
  });
  renderProdutos(filtrados);
}

document.getElementById("busca").addEventListener("input", aplicarFiltros);
document.getElementById("filtro-categoria").addEventListener("change", aplicarFiltros);

// ---------- Produto: criar/editar ----------
const modalProduto = new bootstrap.Modal(document.getElementById("modal-produto"));
const formProduto = document.getElementById("form-produto");

document.getElementById("btn-novo-produto").addEventListener("click", () => {
  formProduto.reset();
  document.getElementById("produto-id").value = "";
  document.getElementById("produto-unidade").value = "UN";
  popularSelectComNovo(document.getElementById("produto-categoria"), categoriasCache, "", "Sem categoria", "+ Nova categoria...");
  popularSelectComNovo(document.getElementById("produto-fornecedor"), fornecedoresCache, "", "Sem fornecedor", "+ Novo fornecedor...");
  popularSelectComNovo(document.getElementById("produto-localizacao"), localizacoesCache, "", "Sem localizacao", "+ Novo local...");
  document.getElementById("modal-produto-title").textContent = "Novo produto";
});

function preencherFormularioEdicao(produto) {
  document.getElementById("produto-id").value = produto.id;
  document.getElementById("produto-nome").value = produto.nome;
  document.getElementById("produto-codigo-barras").value = produto.codigo_barras || "";
  document.getElementById("produto-marca").value = produto.marca || "";
  document.getElementById("produto-unidade").value = produto.unidade_medida;
  document.getElementById("produto-preco-custo").value = produto.preco_custo;
  document.getElementById("produto-preco-venda").value = produto.preco_venda;
  document.getElementById("produto-estoque-minimo").value = produto.estoque_minimo;
  popularSelectComNovo(document.getElementById("produto-categoria"), categoriasCache, produto.categoria_id, "Sem categoria", "+ Nova categoria...");
  popularSelectComNovo(document.getElementById("produto-fornecedor"), fornecedoresCache, produto.fornecedor_id, "Sem fornecedor", "+ Novo fornecedor...");
  popularSelectComNovo(document.getElementById("produto-localizacao"), localizacoesCache, produto.localizacao_id, "Sem localizacao", "+ Novo local...");
  document.getElementById("modal-produto-title").textContent = "Editar produto";
  modalProduto.show();
}

window.abrirEdicaoProduto = function (id) {
  const produto = produtosCache.find((p) => p.id === id);
  if (!produto) return;
  preencherFormularioEdicao(produto);
};

function abrirNovoProdutoComCodigo(codigo) {
  formProduto.reset();
  document.getElementById("produto-id").value = "";
  document.getElementById("produto-unidade").value = "UN";
  popularSelectComNovo(document.getElementById("produto-categoria"), categoriasCache, "", "Sem categoria", "+ Nova categoria...");
  popularSelectComNovo(document.getElementById("produto-fornecedor"), fornecedoresCache, "", "Sem fornecedor", "+ Novo fornecedor...");
  popularSelectComNovo(document.getElementById("produto-localizacao"), localizacoesCache, "", "Sem localizacao", "+ Novo local...");
  document.getElementById("produto-codigo-barras").value = codigo;
  document.getElementById("modal-produto-title").textContent = "Novo produto";
  modalProduto.show();
}

window.removerProduto = async function (id, nome) {
  if (!confirm(`Remover "${nome}"? Esta acao nao pode ser desfeita.`)) return;
  try {
    await Api.produtos.remove(id);
    toast("Produto removido com sucesso.");
    carregarProdutos();
  } catch (err) {
    toast(err.message || "Nao foi possivel remover o produto.", "danger");
  }
};

formProduto.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("produto-id").value;
  const payload = {
    nome: document.getElementById("produto-nome").value.trim(),
    codigo_barras: document.getElementById("produto-codigo-barras").value.trim() || null,
    marca: document.getElementById("produto-marca").value.trim() || null,
    categoria_id: document.getElementById("produto-categoria").value || null,
    fornecedor_id: document.getElementById("produto-fornecedor").value || null,
    localizacao_id: document.getElementById("produto-localizacao").value || null,
    unidade_medida: document.getElementById("produto-unidade").value.trim() || "UN",
    preco_custo: document.getElementById("produto-preco-custo").value || 0,
    preco_venda: document.getElementById("produto-preco-venda").value || 0,
    estoque_minimo: document.getElementById("produto-estoque-minimo").value || 0,
  };

  try {
    if (id) {
      await Api.produtos.update(id, payload);
      toast("Produto atualizado com sucesso.");
    } else {
      await Api.produtos.create(payload);
      toast("Produto cadastrado com sucesso.");
    }
    modalProduto.hide();
    carregarProdutos();
  } catch (err) {
    toast(err.message || "Nao foi possivel cadastrar o produto.", "danger");
  }
});

// ---------- Lote ----------
const modalLote = new bootstrap.Modal(document.getElementById("modal-lote"));
const formLote = document.getElementById("form-lote");

window.abrirNovoLote = function (produtoId, produtoNome) {
  formLote.reset();
  document.getElementById("lote-produto-id").value = produtoId;
  document.getElementById("lote-produto-nome").textContent = produtoNome;
  modalLote.show();
};

formLote.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    produto_id: document.getElementById("lote-produto-id").value,
    numero_lote: document.getElementById("lote-numero").value.trim(),
    quantidade: Number(document.getElementById("lote-quantidade").value),
    custo_unitario: document.getElementById("lote-custo").value,
    data_validade: document.getElementById("lote-validade").value,
  };
  try {
    await Api.lotes.create(payload);
    toast("Lote cadastrado com sucesso.");
    modalLote.hide();
    carregarProdutos();
  } catch (err) {
    toast(err.message || "Nao foi possivel cadastrar o lote.", "danger");
  }
});

// ---------- Escanear codigo de barras ----------
const modalScan = new bootstrap.Modal(document.getElementById("modal-scan"));
let scanner = null;
let scanModo = "lookup"; // "lookup" (fab: busca/cadastra) ou "fill" (dentro do form: so preenche o campo)
let scanEmAndamento = false;

async function pararScanner() {
  if (scanner) {
    try {
      await scanner.stop();
      scanner.clear();
    } catch (e) {
      // camera ja parada / modal fechado antes da camera terminar de iniciar
    }
    scanner = null;
  }
}

async function onCodigoEscaneado(codigoDecodificado) {
  if (scanEmAndamento) return;
  scanEmAndamento = true;
  await pararScanner();
  modalScan.hide();

  if (scanModo === "fill") {
    document.getElementById("produto-codigo-barras").value = codigoDecodificado;
    toast("Codigo capturado.");
    scanEmAndamento = false;
    return;
  }

  try {
    const produto = await Api.produtos.porCodigoBarras(codigoDecodificado);
    if (produto) {
      toast(`Produto encontrado: ${produto.nome}`);
      preencherFormularioEdicao(produto);
    } else {
      toast("Codigo nao cadastrado ainda. Preencha os dados do produto.", "info");
      abrirNovoProdutoComCodigo(codigoDecodificado);
    }
  } catch (err) {
    toast(err.message || "Nao foi possivel buscar o produto.", "danger");
  } finally {
    scanEmAndamento = false;
  }
}

async function abrirScanner(modo) {
  if (typeof Html5Qrcode === "undefined") {
    toast("Leitor de codigo de barras nao carregou. Verifique sua conexao e tente novamente.", "danger");
    return;
  }
  scanModo = modo;
  scanEmAndamento = false;
  document.getElementById("scan-status").textContent = "Aponte a camera para o codigo de barras.";
  modalScan.show();

  scanner = new Html5Qrcode("scan-reader", { verbose: false });
  try {
    await scanner.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 260, height: 140 } },
      onCodigoEscaneado,
      () => {} // callback de "nao achou nada neste frame", chamado o tempo todo enquanto escaneia - ignorar
    );
  } catch (err) {
    document.getElementById("scan-status").textContent = "Nao foi possivel acessar a camera.";
    toast("Nao foi possivel acessar a camera. Verifique se voce deu permissao ao navegador.", "danger");
  }
}

document.getElementById("modal-scan").addEventListener("hidden.bs.modal", () => {
  pararScanner();
  // modo "fill": o form de produto ficou escondido enquanto a camera estava aberta (sucesso ou cancelamento) - reabre com o que ja tiver preenchido.
  if (scanModo === "fill") modalProduto.show();
});

document.getElementById("btn-fab-scan").addEventListener("click", () => abrirScanner("lookup"));
document.getElementById("btn-scan-produto").addEventListener("click", () => {
  modalProduto.hide();
  abrirScanner("fill");
});

ligarCriacaoRapida(document.getElementById("produto-categoria"), {
  getCache: () => categoriasCache,
  setCache: (novaLista) => { categoriasCache = novaLista; popularFiltroCategorias(); },
  apiCriar: Api.categorias.create,
  placeholder: "Sem categoria",
  rotuloNovo: "+ Nova categoria...",
  pergunta: "Nome da nova categoria:",
});
ligarCriacaoRapida(document.getElementById("produto-fornecedor"), {
  getCache: () => fornecedoresCache,
  setCache: (novaLista) => { fornecedoresCache = novaLista; },
  apiCriar: Api.fornecedores.create,
  placeholder: "Sem fornecedor",
  rotuloNovo: "+ Novo fornecedor...",
  pergunta: "Nome do novo fornecedor:",
});
ligarCriacaoRapida(document.getElementById("produto-localizacao"), {
  getCache: () => localizacoesCache,
  setCache: (novaLista) => { localizacoesCache = novaLista; },
  apiCriar: Api.localizacoes.create,
  placeholder: "Sem localizacao",
  rotuloNovo: "+ Novo local...",
  pergunta: "Nome do novo local (ex: Geladeira 2, Corredor 3):",
});

(async function () {
  await carregarListasAuxiliares();
  await carregarProdutos();
})();
