initNav("mais");

let cache = [];

function render(itens) {
  const el = document.getElementById("vs-lista");
  if (!itens.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">🏷</div>Nenhuma categoria cadastrada.<br><span class="small">Crie sua primeira categoria para organizar os produtos.</span></div>`;
    return;
  }
  el.innerHTML = itens.map((c) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${c.nome}</div>
          <div class="vs-list-card-meta">${c.total_produtos} produto${c.total_produtos === 1 ? "" : "s"}${c.descricao ? ` · ${c.descricao}` : ""}</div>
        </div>
      </div>
      <div class="d-flex gap-2 mt-2">
        <button class="btn btn-sm btn-outline-secondary" onclick="abrirEdicao('${c.id}')">Editar</button>
        <button class="btn btn-sm btn-outline-danger" onclick="desativar('${c.id}', '${c.nome.replace(/'/g, "\\'")}')">Desativar</button>
      </div>
    </div>
  `).join("");
}

async function carregar() {
  try {
    cache = await Api.categorias.list();
    aplicarFiltro();
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-lista").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar categorias.", "danger");
  }
}

function aplicarFiltro() {
  const termo = document.getElementById("busca").value.trim().toLowerCase();
  render(cache.filter((c) => !termo || c.nome.toLowerCase().includes(termo)));
}
document.getElementById("busca").addEventListener("input", aplicarFiltro);

const modal = new bootstrap.Modal(document.getElementById("modal-categoria"));
const form = document.getElementById("form-categoria");

document.getElementById("btn-nova").addEventListener("click", () => {
  form.reset();
  document.getElementById("categoria-id").value = "";
  document.getElementById("modal-title").textContent = "Nova categoria";
});

window.abrirEdicao = function (id) {
  const c = cache.find((x) => x.id === id);
  if (!c) return;
  document.getElementById("categoria-id").value = c.id;
  document.getElementById("categoria-nome").value = c.nome;
  document.getElementById("categoria-descricao").value = c.descricao || "";
  document.getElementById("modal-title").textContent = "Editar categoria";
  modal.show();
};

window.desativar = async function (id, nome) {
  if (!confirm(`Desativar a categoria "${nome}"? Produtos ja cadastrados nela permanecem intactos.`)) return;
  try {
    await Api.categorias.remove(id);
    toast("Categoria desativada.");
    carregar();
  } catch (err) {
    toast(err.message || "Nao foi possivel desativar a categoria.", "danger");
  }
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("categoria-id").value;
  const payload = {
    nome: document.getElementById("categoria-nome").value.trim(),
    descricao: document.getElementById("categoria-descricao").value.trim() || null,
  };
  try {
    if (id) {
      await Api.categorias.update(id, payload);
      toast("Categoria atualizada.");
    } else {
      await Api.categorias.create(payload);
      toast("Categoria criada com sucesso.");
    }
    modal.hide();
    carregar();
  } catch (err) {
    toast(err.message || "Nao foi possivel salvar a categoria.", "danger");
  }
});

carregar();
