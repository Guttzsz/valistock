initNav("produtos");

let produtosCache = [];
let categoriasCache = [];
let fornecedoresCache = [];
let localizacoesCache = [];

function renderProdutos(produtos) {
  const container = document.getElementById("vs-produtos-list");
  if (!produtos.length) {
    container.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">📦</div>Nenhum produto encontrado.<br><span class="small">Cadastre seu primeiro produto para comecar.</span></div>`;
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
      <div class="d-flex gap-2 flex-wrap">
        <button class="btn btn-sm btn-outline-secondary" onclick="abrirEdicaoProduto('${p.id}')">Editar</button>
        <button class="btn btn-sm btn-vs-primary" onclick="abrirNovoLote('${p.id}', '${p.nome.replace(/'/g, "\\'")}')">+ Lote</button>
        <button class="btn btn-sm btn-outline-danger" onclick="removerProduto('${p.id}', '${p.nome.replace(/'/g, "\\'")}')">Excluir</button>
      </div>
    </div>
  `).join("");
}

function popularSelect(select, itens, valorAtual, placeholder) {
  const atual = valorAtual !== undefined ? valorAtual : select.value;
  select.innerHTML = `<option value="">${placeholder}</option>` + itens.map((i) => `<option value="${i.id}">${i.nome}</option>`).join("");
  select.value = atual || "";
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
    popularSelect(document.getElementById("produto-categoria"), categoriasCache, "", "Sem categoria");
    popularSelect(document.getElementById("produto-fornecedor"), fornecedoresCache, "", "Sem fornecedor");
    popularSelect(document.getElementById("produto-localizacao"), localizacoesCache, "", "Sem localizacao");
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
  popularSelect(document.getElementById("produto-categoria"), categoriasCache, "", "Sem categoria");
  popularSelect(document.getElementById("produto-fornecedor"), fornecedoresCache, "", "Sem fornecedor");
  popularSelect(document.getElementById("produto-localizacao"), localizacoesCache, "", "Sem localizacao");
  document.getElementById("modal-produto-title").textContent = "Novo produto";
});

window.abrirEdicaoProduto = function (id) {
  const produto = produtosCache.find((p) => p.id === id);
  if (!produto) return;
  document.getElementById("produto-id").value = produto.id;
  document.getElementById("produto-nome").value = produto.nome;
  document.getElementById("produto-codigo-barras").value = produto.codigo_barras || "";
  document.getElementById("produto-marca").value = produto.marca || "";
  document.getElementById("produto-unidade").value = produto.unidade_medida;
  document.getElementById("produto-preco-custo").value = produto.preco_custo;
  document.getElementById("produto-preco-venda").value = produto.preco_venda;
  document.getElementById("produto-estoque-minimo").value = produto.estoque_minimo;
  popularSelect(document.getElementById("produto-categoria"), categoriasCache, produto.categoria_id, "Sem categoria");
  popularSelect(document.getElementById("produto-fornecedor"), fornecedoresCache, produto.fornecedor_id, "Sem fornecedor");
  popularSelect(document.getElementById("produto-localizacao"), localizacoesCache, produto.localizacao_id, "Sem localizacao");
  document.getElementById("modal-produto-title").textContent = "Editar produto";
  modalProduto.show();
};

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

// ---------- Escanear codigo de barras (preparado para Fase 2) ----------
function avisoScanIndisponivel() {
  toast("Leitura por camera sera adicionada em uma proxima atualizacao. Digite o codigo manualmente por enquanto.", "info");
}
document.getElementById("btn-fab-scan").addEventListener("click", avisoScanIndisponivel);
document.getElementById("btn-scan-produto").addEventListener("click", avisoScanIndisponivel);

(async function () {
  await carregarListasAuxiliares();
  await carregarProdutos();
})();
