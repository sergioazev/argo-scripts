const $ = (id) => document.getElementById(id);

const escapeHtml = (s) => String(s ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const log = (data) => {
  const el = $("log");
  if (!el) return;
  if (typeof data === "string") {
    el.textContent = data;
  } else {
    el.textContent = JSON.stringify(data, null, 2);
  }
};

function renderRenameTable(items, extra = "") {
  const rows = items.map(item => {
    const statusClass = `status-${item.status}`;
    return `
      <tr>
        <td>${item.index}</td>
        <td>${escapeHtml(item.oldName)}</td>
        <td><strong>${escapeHtml(item.newName)}</strong></td>
        <td class="${statusClass}">${escapeHtml(item.status)}</td>
      </tr>
    `;
  }).join("");

  $("log").innerHTML = `
    ${extra ? `<p class="small">${escapeHtml(extra)}</p>` : ""}
    <table class="rename-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Antes</th>
          <th>Depois</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderStructurePreview(data) {
  $("log").innerHTML = `
    <p><strong>Destino:</strong> ${escapeHtml(data.destination)}</p>
    <p><strong>Itens:</strong> ${data.count}</p>
    <table class="rename-table">
      <thead><tr><th>#</th><th>Pasta / arquivo</th></tr></thead>
      <tbody>
        ${data.paths.map((p, i) => `<tr><td>${i + 1}</td><td>${escapeHtml(p)}</td></tr>`).join("")}
      </tbody>
    </table>
  `;
}

function getStructureOpts() {
  return {
    title: $("title").value,
    root: $("root").value,
    date: $("date").value,
    mode: $("mode").value,
    template: $("template").value,
    sourceRoot: $("sourceRoot").value,
    manualText: $("manual").value
  };
}

function getRenameOpts() {
  return {
    title: $("title").value,
    renameFolder: $("renameFolder").value,
    useFfprobe: $("useFfprobe").checked,
    includeAllFiles: $("includeAllFiles").checked,
    renameMode: $("renameMode").value,
    addText: $("addText").value,
    findText: $("findText").value,
    replaceText: $("replaceText").value,
    replaceFullName: $("replaceFullName").value,
    sequencePrefix: $("sequencePrefix").value,
    sequenceStart: $("sequenceStart").value,
    sequenceDigits: $("sequenceDigits").value,
    lowercase: $("lowercase").checked,
    keepExtension: $("keepExtension").checked
  };
}

function setButton(id, handler) {
  const btn = $(id);
  if (!btn) {
    log(`ERRO: botão não encontrado: ${id}`);
    return;
  }
  btn.addEventListener("click", handler);
}

async function init() {
  try {
    if (!window.argo) {
      throw new Error("Preload não carregou. Feche o app, rode 'npm install' novamente e execute 'npm start'.");
    }

    const templates = await window.argo.listTemplates();
    $("template").innerHTML = templates.map(t => `<option value="${t}">${t}</option>`).join("");

    $("date").value = await window.argo.today();

    const home = await window.argo.home();
    $("root").value = `${home}/Movies/ARGO_ORGANIZADOR`;

    setButton("chooseRoot", async () => {
      try {
        const p = await window.argo.chooseFolder();
        if (p) $("root").value = p;
      } catch (e) {
        log(`ERRO AO ESCOLHER DESTINO:\n${e.message}`);
      }
    });

    setButton("chooseSource", async () => {
      try {
        const p = await window.argo.chooseFolder();
        if (p) {
          $("sourceRoot").value = p;
          $("mode").value = "copy";
        }
      } catch (e) {
        log(`ERRO AO ESCOLHER MODELO:\n${e.message}`);
      }
    });

    setButton("chooseRenameFolder", async () => {
      try {
        const p = await window.argo.chooseFolder();
        if (p) $("renameFolder").value = p;
      } catch (e) {
        log(`ERRO AO ESCOLHER PASTA DE RENAME:\n${e.message}`);
      }
    });

    setButton("chooseRollback", async () => {
      try {
        const p = await window.argo.chooseRollback();
        if (p) $("rollbackFile").value = p;
      } catch (e) {
        log(`ERRO AO ESCOLHER ROLLBACK:\n${e.message}`);
      }
    });

    setButton("previewStructure", async () => {
      try { renderStructurePreview(await window.argo.previewStructure(getStructureOpts())); }
      catch (e) { log(`ERRO:\n${e.message}`); }
    });

    setButton("applyStructure", async () => {
      try { log(await window.argo.applyStructure(getStructureOpts())); }
      catch (e) { log(`ERRO:\n${e.message}`); }
    });

    setButton("previewRename", async () => {
      try {
        const items = await window.argo.previewRename(getRenameOpts());
        renderRenameTable(items, `${items.length} arquivos analisados. Nada foi renomeado.`);
      }
      catch (e) { log(`ERRO:\n${e.message}`); }
    });

    setButton("applyRename", async () => {
      try {
        const result = await window.argo.applyRename(getRenameOpts());
        renderRenameTable(result.applied, result.blocked ? result.message : `Rollback salvo em: ${result.rollbackPath}`);
      }
      catch (e) { log(`ERRO:\n${e.message}`); }
    });

    setButton("rollback", async () => {
      try { log(await window.argo.rollback($("rollbackFile").value)); }
      catch (e) { log(`ERRO:\n${e.message}`); }
    });

    log("Pronto. Rename visual V1.3 ativo.");
  } catch (e) {
    log(`ERRO NA INICIALIZAÇÃO DO APP:\n${e.message}`);
  }
}

window.addEventListener("DOMContentLoaded", init);
