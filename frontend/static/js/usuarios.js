initNav("mais");

const PERFIL_LABELS = { administrador: "Administrador", gerente: "Gerente", funcionario: "Funcionario" };

function renderUsuarios(usuarios) {
  const el = document.getElementById("vs-usuarios-list");
  const tbody = document.querySelector("#vs-usuarios-table tbody");
  const euSouAdmin = Auth.getUser()?.perfil === "administrador";

  if (!usuarios.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 vs-muted">Nenhum usuario cadastrado.</td></tr>`;
  }

  el.innerHTML = usuarios.map((u) => `
    <div class="vs-list-card">
      <div class="vs-list-card-top">
        <div>
          <div class="vs-list-card-title">${u.nome} ${!u.ativo ? '<span class="vs-badge neutro">Inativo</span>' : ""}</div>
          <div class="vs-list-card-meta">${u.email} · ${u.cargo || "-"}</div>
        </div>
        <span class="vs-badge normal">${PERFIL_LABELS[u.perfil] || u.perfil}</span>
      </div>
      ${euSouAdmin ? `<button class="btn btn-sm btn-outline-danger mt-2" onclick="removerUsuario('${u.id}','${u.nome.replace(/'/g, "\\'")}')">Remover</button>` : ""}
    </div>
  `).join("");

  tbody.innerHTML = usuarios.map((u) => `
    <tr>
      <td>${u.nome}</td>
      <td>${u.email}</td>
      <td>${u.cargo || "-"}</td>
      <td><span class="vs-badge normal">${PERFIL_LABELS[u.perfil] || u.perfil}</span></td>
      <td>${u.ativo ? `<span class="vs-badge normal">Ativo</span>` : `<span class="vs-badge neutro">Inativo</span>`}</td>
      <td>${euSouAdmin ? `<button class="btn btn-sm btn-outline-danger" onclick="removerUsuario('${u.id}','${u.nome.replace(/'/g, "\\'")}')">Remover</button>` : "-"}</td>
    </tr>
  `).join("");
}

async function carregarUsuarios() {
  try {
    const usuarios = await Api.usuarios.list();
    renderUsuarios(usuarios);
    document.getElementById("vs-loading").classList.add("d-none");
    document.getElementById("vs-usuarios-list").classList.remove("d-none");
  } catch (err) {
    toast(err.message || "Erro ao carregar usuarios.", "danger");
  }
}

window.removerUsuario = async function (id, nome) {
  if (!confirm(`Remover "${nome}"?`)) return;
  try {
    await Api.usuarios.remove(id);
    toast("Usuario removido.");
    carregarUsuarios();
  } catch (err) {
    toast(err.message || "Voce nao possui permissao para realizar esta acao.", "danger");
  }
};

document.getElementById("form-usuario").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    nome: document.getElementById("usuario-nome").value.trim(),
    email: document.getElementById("usuario-email").value.trim(),
    senha: document.getElementById("usuario-senha").value,
    cargo: document.getElementById("usuario-cargo").value.trim() || null,
    perfil: document.getElementById("usuario-perfil").value,
  };
  try {
    await Api.usuarios.create(payload);
    toast("Usuario cadastrado com sucesso.");
    bootstrap.Modal.getInstance(document.getElementById("modal-usuario")).hide();
    document.getElementById("form-usuario").reset();
    carregarUsuarios();
  } catch (err) {
    toast(err.message || "Nao foi possivel cadastrar o usuario.", "danger");
  }
});

carregarUsuarios();
