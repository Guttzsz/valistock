initNav("mais");

let cache = [];

function render(itens) {
  const el = document.getElementById("vs-lista");
  if (!itens.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("truck", { size: 24 })}</div>Nenhum fornecedor cadastrado.</div>`;
    return;
  }
  el.innerHTML = itens.map((f) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${f.nome}</div>
          <div class="vs-list-card-meta">${f.total_produtos} produto${f.total_produtos === 1 ? "" : "s"}${f.telefone ? ` · ${f.telefone}` : ""}${f.email ? ` · ${f.email}` : ""}</div>
        </div>
      </div>
      <div class="d-flex gap-2 mt-2">
        <button class="btn btn-sm btn-outline-secondary" onclick="abrirEdicao('${f.id}')">Editar</button>
        <button class="btn btn-sm btn-outline-danger" onclick="desativar('${f.id}', '${f.nome.replace(/'/g, "\\'")}')">Desativar</button>
      </div>
    </div>
  `).join("");
}

async function carregar() {
  try {
    cache = await Api.fornecedores.list();
    aplicarFiltro();
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-lista").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar fornecedores.", "danger");
  }
}

function aplicarFiltro() {
  const termo = document.getElementById("busca").value.trim().toLowerCase();
  render(cache.filter((f) => !termo || f.nome.toLowerCase().includes(termo)));
}
document.getElementById("busca").addEventListener("input", aplicarFiltro);

const modal = new bootstrap.Modal(document.getElementById("modal-fornecedor"));
const form = document.getElementById("form-fornecedor");

document.getElementById("btn-novo").addEventListener("click", () => {
  form.reset();
  document.getElementById("fornecedor-id").value = "";
  document.getElementById("modal-title").textContent = "Novo fornecedor";
});

window.abrirEdicao = function (id) {
  const f = cache.find((x) => x.id === id);
  if (!f) return;
  document.getElementById("fornecedor-id").value = f.id;
  document.getElementById("fornecedor-nome").value = f.nome;
  document.getElementById("fornecedor-razao").value = f.razao_social || "";
  document.getElementById("fornecedor-cnpj").value = f.cnpj || "";
  document.getElementById("fornecedor-telefone").value = f.telefone || "";
  document.getElementById("fornecedor-email").value = f.email || "";
  document.getElementById("fornecedor-endereco").value = f.endereco || "";
  document.getElementById("fornecedor-observacao").value = f.observacao || "";
  document.getElementById("modal-title").textContent = "Editar fornecedor";
  modal.show();
};

window.desativar = async function (id, nome) {
  if (!confirm(`Desativar o fornecedor "${nome}"?`)) return;
  try {
    await Api.fornecedores.remove(id);
    toast("Fornecedor desativado.");
    carregar();
  } catch (err) {
    toast(err.message || "Nao foi possivel desativar o fornecedor.", "danger");
  }
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("fornecedor-id").value;
  const payload = {
    nome: document.getElementById("fornecedor-nome").value.trim(),
    razao_social: document.getElementById("fornecedor-razao").value.trim() || null,
    cnpj: document.getElementById("fornecedor-cnpj").value.trim() || null,
    telefone: document.getElementById("fornecedor-telefone").value.trim() || null,
    email: document.getElementById("fornecedor-email").value.trim() || null,
    endereco: document.getElementById("fornecedor-endereco").value.trim() || null,
    observacao: document.getElementById("fornecedor-observacao").value.trim() || null,
  };
  try {
    if (id) {
      await Api.fornecedores.update(id, payload);
      toast("Fornecedor atualizado.");
    } else {
      await Api.fornecedores.create(payload);
      toast("Fornecedor cadastrado com sucesso.");
    }
    modal.hide();
    carregar();
  } catch (err) {
    toast(err.message || "Nao foi possivel salvar o fornecedor.", "danger");
  }
});

carregar();
