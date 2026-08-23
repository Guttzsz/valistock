initNav("mais");

let cache = [];

function acoesLocalHtml(l) {
  return `
    <button class="btn btn-sm btn-outline-secondary" onclick="abrirEdicao('${l.id}')">Editar</button>
    <button class="btn btn-sm btn-outline-danger" onclick="desativar('${l.id}', '${l.nome.replace(/'/g, "\\'")}')">Desativar</button>
  `;
}

function render(itens) {
  const el = document.getElementById("vs-lista");
  const tbody = document.querySelector("#vs-localizacoes-table tbody");
  if (!itens.length) {
    el.innerHTML = `<div class="vs-empty"><div class="vs-empty-icon">${VsIcon("mapPin", { size: 24 })}</div>Nenhum local cadastrado.<br><span class="small">Ex: Corredor 1, Geladeira 2, Freezer, Estoque.</span></div>`;
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 vs-muted">Nenhum local cadastrado.</td></tr>`;
    return;
  }
  el.innerHTML = itens.map((l) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${l.nome}</div>
          <div class="vs-list-card-meta">${l.tipo || ""}${l.descricao ? ` · ${l.descricao}` : ""}</div>
        </div>
      </div>
      <div class="d-flex gap-2 mt-2">${acoesLocalHtml(l)}</div>
    </div>
  `).join("");

  tbody.innerHTML = itens.map((l) => `
    <tr>
      <td>${l.nome}</td>
      <td>${l.tipo || "-"}</td>
      <td>${l.descricao || "-"}</td>
      <td><div class="d-flex gap-2 flex-wrap">${acoesLocalHtml(l)}</div></td>
    </tr>
  `).join("");
}

async function carregar() {
  try {
    cache = await Api.localizacoes.list();
    render(cache);
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-lista").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar locais.", "danger");
  }
}

const modal = new bootstrap.Modal(document.getElementById("modal-local"));
const form = document.getElementById("form-local");

document.getElementById("btn-novo").addEventListener("click", () => {
  form.reset();
  document.getElementById("local-id").value = "";
  document.getElementById("modal-title").textContent = "Novo local";
});

window.abrirEdicao = function (id) {
  const l = cache.find((x) => x.id === id);
  if (!l) return;
  document.getElementById("local-id").value = l.id;
  document.getElementById("local-nome").value = l.nome;
  document.getElementById("local-tipo").value = l.tipo || "";
  document.getElementById("local-descricao").value = l.descricao || "";
  document.getElementById("modal-title").textContent = "Editar local";
  modal.show();
};

window.desativar = async function (id, nome) {
  if (!confirm(`Desativar o local "${nome}"?`)) return;
  try {
    await Api.localizacoes.remove(id);
    toast("Local desativado.");
    carregar();
  } catch (err) {
    toast(err.message || "Nao foi possivel desativar o local.", "danger");
  }
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("local-id").value;
  const payload = {
    nome: document.getElementById("local-nome").value.trim(),
    tipo: document.getElementById("local-tipo").value.trim() || null,
    descricao: document.getElementById("local-descricao").value.trim() || null,
  };
  try {
    if (id) {
      await Api.localizacoes.update(id, payload);
      toast("Local atualizado.");
    } else {
      await Api.localizacoes.create(payload);
      toast("Local cadastrado com sucesso.");
    }
    modal.hide();
    carregar();
  } catch (err) {
    toast(err.message || "Nao foi possivel salvar o local.", "danger");
  }
});

carregar();
