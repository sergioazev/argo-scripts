const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { TEMPLATES } = require("./templates");

const MEDIA_EXTS = new Set([
  ".mov", ".mp4", ".mxf", ".mkv", ".avi",
  ".wav", ".aif", ".aiff",
  ".dpx", ".exr", ".tif", ".tiff",
  ".srt", ".xml", ".edl", ".otio"
]);

function slugify(input) {
  let text = String(input || "").trim().toLowerCase();
  text = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  text = text.replace(/^(a|o|as|os)\s+/i, "");
  text = text.replace(/[^a-z0-9._-]+/g, "_");
  text = text.replace(/_+/g, "_").replace(/^_+|_+$/g, "");
  return text;
}

function safeName(input) {
  let text = String(input || "");
  text = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  text = text.replace(/[^a-zA-Z0-9._ -]+/g, "_");
  text = text.replace(/\s+/g, "_");
  text = text.replace(/_+/g, "_").replace(/^_+|_+$/g, "");
  return text;
}

function today() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
}

function isPlaceholder(rel) {
  const base = path.basename(rel).toLowerCase();
  return base.endsWith(".placeholder") || base === "checksum.txt";
}

function render(rel, vars) {
  return rel.replaceAll("{slug}", vars.slug).replaceAll("{date}", vars.date);
}

function listFolderStructureOnly(sourceRoot) {
  const out = [];
  function walk(current) {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const e of entries) {
      if (e.name.startsWith(".")) continue;
      if (e.isDirectory()) {
        const full = path.join(current, e.name);
        const rel = path.relative(sourceRoot, full).split(path.sep).join("/");
        out.push(rel);
        walk(full);
      }
    }
  }
  walk(sourceRoot);
  return [...new Set(out)].sort();
}

function normalizeManual(text) {
  return [...new Set(
    String(text || "")
      .split(/\r?\n/)
      .map(s => s.trim().replaceAll("\\", "/").replace(/^\/+|\/+$/g, ""))
      .filter(s => s && !s.startsWith("#"))
  )].sort();
}

function buildPaths(opts) {
  const slug = slugify(opts.title);
  const date = opts.date || today();

  if (!/^\d{8}$/.test(date)) throw new Error("Data inválida. Use YYYYMMDD.");

  if (opts.mode === "template") {
    const t = TEMPLATES[opts.template];
    if (!t) throw new Error("Template inexistente.");
    return t.map(p => render(p, { slug, date }));
  }

  if (opts.mode === "copy") {
    if (!opts.sourceRoot || !fs.existsSync(opts.sourceRoot)) throw new Error("Pasta modelo não encontrada.");
    return listFolderStructureOnly(opts.sourceRoot);
  }

  if (opts.mode === "manual") {
    return normalizeManual(opts.manualText);
  }

  throw new Error("Modo inválido.");
}

function preview(opts) {
  const slug = slugify(opts.title);
  const destination = path.join(opts.root, slug);
  const paths = buildPaths(opts);
  return { slug, destination, paths, count: paths.length };
}

function applyStructure(opts) {
  const p = preview(opts);
  let createdDirs = 0;
  let existingDirs = 0;
  let createdFiles = 0;
  let existingFiles = 0;

  for (const rel of p.paths) {
    const target = path.join(p.destination, rel);

    if (isPlaceholder(rel)) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      if (fs.existsSync(target)) existingFiles++;
      else {
        fs.writeFileSync(target, "");
        createdFiles++;
      }
    } else {
      if (fs.existsSync(target)) existingDirs++;
      else {
        fs.mkdirSync(target, { recursive: true });
        createdDirs++;
      }
    }
  }

  return { ...p, createdDirs, existingDirs, createdFiles, existingFiles };
}

function scanFiles(folder, includeAll = false) {
  if (!folder || !fs.existsSync(folder)) throw new Error("Pasta de arquivos não encontrada.");
  const entries = fs.readdirSync(folder, { withFileTypes: true });
  return entries
    .filter(e => e.isFile())
    .map(e => path.join(folder, e.name))
    .filter(f => includeAll || MEDIA_EXTS.has(path.extname(f).toLowerCase()))
    .sort((a, b) => path.basename(a).localeCompare(path.basename(b), undefined, { numeric: true }));
}

function ffprobe(file) {
  try {
    const raw = execFileSync("ffprobe", [
      "-v", "quiet",
      "-print_format", "json",
      "-show_format",
      "-show_streams",
      file
    ], { encoding: "utf8", timeout: 10000 });
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function applyRenameRule(baseName, ext, i, opts) {
  let name = baseName;

  const findText = opts.findText || "";
  const replaceText = opts.replaceText || "";

  if (opts.renameMode === "replaceAll") {
    name = safeName(opts.replaceFullName || "");
  }

  if (opts.renameMode === "addBefore") {
    name = `${safeName(opts.addText)}${name}`;
  }

  if (opts.renameMode === "addAfter") {
    name = `${name}${safeName(opts.addText)}`;
  }

  if (opts.renameMode === "findReplace" && findText) {
    name = name.split(findText).join(replaceText);
  }

  if (opts.renameMode === "sequence") {
    const prefix = safeName(opts.sequencePrefix || "");
    const start = Number(opts.sequenceStart || 1);
    const digits = Number(opts.sequenceDigits || 3);
    name = `${prefix}${String(start + i).padStart(digits, "0")}`;
  }

  if (opts.renameMode === "slugSequence") {
    const slug = slugify(opts.title);
    const start = Number(opts.sequenceStart || 1);
    const digits = Number(opts.sequenceDigits || 3);
    const middle = safeName(opts.sequencePrefix || "clip");
    name = `${slug}_${middle}_${String(start + i).padStart(digits, "0")}`;
  }

  if (opts.lowercase) name = name.toLowerCase();

  name = safeName(name);

  const finalExt = opts.keepExtension === false ? "" : ext;
  return `${name}${finalExt}`;
}

function renamePreview(opts) {
  const files = scanFiles(opts.renameFolder, !!opts.includeAllFiles);
  const seen = new Map();

  return files.map((file, i) => {
    const ext = path.extname(file);
    const base = path.basename(file, ext);
    const newName = applyRenameRule(base, ext, i, opts);
    const newPath = path.join(path.dirname(file), newName);

    let status = "ok";
    if (newName === path.basename(file)) status = "unchanged";
    if (fs.existsSync(newPath) && newPath !== file) status = "conflict_exists";
    if (seen.has(newName)) status = "conflict_duplicate";
    seen.set(newName, true);

    return {
      index: i + 1,
      oldPath: file,
      newPath,
      oldName: path.basename(file),
      newName,
      status,
      metadata: opts.useFfprobe ? ffprobe(file) : null
    };
  });
}

function applyRename(opts) {
  const plan = renamePreview(opts);
  const applied = [];

  const hasConflict = plan.some(x => x.status === "conflict_exists" || x.status === "conflict_duplicate");
  if (hasConflict && !opts.allowConflicts) {
    return {
      applied: plan.map(x => ({ ...x, status: x.status === "ok" ? "not_applied" : x.status })),
      rollbackPath: null,
      blocked: true,
      message: "Renomeação bloqueada: existem conflitos no preview."
    };
  }

  for (const item of plan) {
    if (item.status !== "ok") {
      applied.push({ ...item, status: item.status === "unchanged" ? "unchanged" : "skipped" });
      continue;
    }

    fs.renameSync(item.oldPath, item.newPath);
    applied.push({ ...item, status: "renamed" });
  }

  const rollbackPath = path.join(opts.renameFolder, `.argo_rollback_${Date.now()}.json`);
  fs.writeFileSync(rollbackPath, JSON.stringify(applied, null, 2));
  return { applied, rollbackPath, blocked: false };
}

function rollback(rollbackFile) {
  if (!rollbackFile || !fs.existsSync(rollbackFile)) throw new Error("Arquivo de rollback não encontrado.");
  const data = JSON.parse(fs.readFileSync(rollbackFile, "utf8"));
  let restored = 0;
  for (const item of [...data].reverse()) {
    if (item.status === "renamed" && fs.existsSync(item.newPath) && !fs.existsSync(item.oldPath)) {
      fs.renameSync(item.newPath, item.oldPath);
      restored++;
    }
  }
  return { restored };
}

module.exports = {
  TEMPLATES,
  slugify,
  today,
  preview,
  applyStructure,
  renamePreview,
  applyRename,
  rollback
};
