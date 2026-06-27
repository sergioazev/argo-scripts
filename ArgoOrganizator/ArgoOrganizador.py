#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArgoOrganizador.py V5
DaVinci Resolve > Workspace > Scripts > Utility > ArgoOrganizador

Recursos:
- 6 templates técnicos embutidos
- Copiar estrutura existente com botão ESCOLHER...
- Criar estrutura manual
- Preview antes de aplicar
- Criar pastas no disco
- Criar bins no Resolve
- Rename físico com regras tipo Finder/Renamer:
  * Add Before Name
  * Add After Name
  * Find and Replace
  * Sequence
  * Project Slug + Sequence
  * Replace Full Name
- Preview visual do rename
- Bloqueio por conflito
- Rollback por JSON
- Rename opcional de clips do bin atual no Resolve
"""

import os
import re
import json
import unicodedata
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

APP_VERSION = "V5"
DEFAULT_PROJECT_TITLE = "O Cabra Marcado Para Morrer"
DEFAULT_ROOT = str(Path.home() / "Movies" / "ARGO_ORGANIZADOR")
DEFAULT_DATE = datetime.now().strftime("%Y%m%d")
REMOVE_INITIAL_ARTICLES = True

MEDIA_EXTS = {
    ".mov", ".mp4", ".mxf", ".mkv", ".avi",
    ".wav", ".aif", ".aiff",
    ".dpx", ".exr", ".tif", ".tiff",
    ".srt", ".xml", ".edl", ".otio"
}


# ============================================================
# TEMPLATES EMBUTIDOS
# ============================================================

TEMPLATES = {
    "Cinemateca_Deposito_Legal_Cinema": [
        "{slug}_cinemateca",
        "{slug}_cinemateca/{slug}_preservacao",
        "{slug}_cinemateca/{slug}_exibicao",
        "{slug}_cinemateca/recursos_de_acessibilidade",
        "{slug}_cinemateca/recursos_de_acessibilidade/libras",
        "{slug}_cinemateca/recursos_de_acessibilidade/audiodescricao",
        "{slug}_cinemateca/recursos_de_acessibilidade/legendas_descritivas",
        "{slug}_cinemateca/documentacao",
        "{slug}_cinemateca/laudo_tecnico",
        "{slug}_cinemateca/qc"
    ],

    "Cinemateca_Deposito_Legal_TV_Outras_Telas": [
        "{slug}_cinemateca",
        "{slug}_cinemateca/{slug}_preservacao_mkv_ffv1",
        "{slug}_cinemateca/{slug}_copia_acesso",
        "{slug}_cinemateca/recursos_de_acessibilidade",
        "{slug}_cinemateca/recursos_de_acessibilidade/libras",
        "{slug}_cinemateca/recursos_de_acessibilidade/audiodescricao",
        "{slug}_cinemateca/recursos_de_acessibilidade/legendas_descritivas",
        "{slug}_cinemateca/documentacao",
        "{slug}_cinemateca/laudo_tecnico",
        "{slug}_cinemateca/qc"
    ],

    "Netflix_Picture_Archival_NAM_Longplay": [
        "{slug}_nam_16b_rwg_log3g10_{date}_3840x2160",
        "{slug}_nam_16b_rwg_log3g10_{date}_3840x2160/checksum.txt.placeholder"
    ],

    "Netflix_Picture_Archival_DCDM_Reels": [
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r01/checksum.txt.placeholder",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r02/checksum.txt.placeholder",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r03/checksum.txt.placeholder",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r04/checksum.txt.placeholder"
    ],

    "Netflix_IMF_Delivery": [
        "{slug}_imf_delivery",
        "{slug}_imf_delivery/ASSETMAP",
        "{slug}_imf_delivery/PKL",
        "{slug}_imf_delivery/CPL",
        "{slug}_imf_delivery/OPL_optional",
        "{slug}_imf_delivery/MXF",
        "{slug}_imf_delivery/QC/reports"
    ],

    "DCP_SMPTE_DCI_Package": [
        "{slug}_dcp_smpte",
        "{slug}_dcp_smpte/CPL",
        "{slug}_dcp_smpte/PKL",
        "{slug}_dcp_smpte/ASSETMAP",
        "{slug}_dcp_smpte/VOLINDEX",
        "{slug}_dcp_smpte/MXF/picture",
        "{slug}_dcp_smpte/MXF/audio",
        "{slug}_dcp_smpte/MXF/subtitles",
        "{slug}_dcp_smpte/QC"
    ]
}

DEFAULT_MANUAL_STRUCTURE = """00_ADMIN
01_BRUTOS
01_BRUTOS/CAMERA_A
01_BRUTOS/CAMERA_B
02_AUDIO
03_PROXIES
04_SYNC
05_TIMELINES
06_EXPORTS
07_MASTER
08_QC
09_ARCHIVE"""


# ============================================================
# RESOLVE API
# ============================================================

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except Exception:
    resolve = globals().get("resolve", None)

if not resolve:
    try:
        resolve = bmd.scriptapp("Resolve")
    except Exception:
        resolve = None


# ============================================================
# UTIL
# ============================================================

def slugify(text):
    text = str(text or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    if REMOVE_INITIAL_ARTICLES:
        text = re.sub(r"^(a|o|as|os)\s+", "", text)

    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def safe_name(text):
    text = str(text or "")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-zA-Z0-9._ -]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def validate_date(date_text):
    if not re.match(r"^\d{8}$", str(date_text or "")):
        raise Exception("Data inválida. Use YYYYMMDD, exemplo: 20260501.")
    return date_text


def render_path(path_template, slug, date):
    return path_template.replace("{slug}", slug).replace("{date}", date)


def is_placeholder_file(path_value):
    name = Path(str(path_value)).name.lower()
    return name.endswith(".placeholder") or name == "checksum.txt"


def normalize_manual_lines(text):
    lines = []
    for line in str(text or "").splitlines():
        clean = line.strip().strip("/").strip()
        if not clean or clean.startswith("#"):
            continue
        clean = clean.replace("\\", "/")
        lines.append(clean)
    return sorted(set(lines))


def short_status(status):
    labels = {
        "ok": "OK",
        "unchanged": "SEM MUDANÇA",
        "conflict_exists": "CONFLITO: JÁ EXISTE",
        "conflict_duplicate": "CONFLITO: DUPLICADO",
        "renamed": "RENOMEADO",
        "skipped": "IGNORADO",
        "not_applied": "NÃO APLICADO"
    }
    return labels.get(status, status)


# ============================================================
# ESTRUTURA DE PASTAS
# ============================================================

def collect_folder_structure(source_root):
    source_root = Path(source_root)

    if not source_root.exists():
        raise Exception(f"Pasta modelo não encontrada:\n{source_root}")

    if not source_root.is_dir():
        raise Exception(f"O caminho escolhido não é uma pasta:\n{source_root}")

    paths = []

    for root, dirs, files in os.walk(source_root):
        relative = Path(root).relative_to(source_root)

        if str(relative) != ".":
            paths.append(str(relative).replace("\\", "/"))

        for d in dirs:
            if d.startswith("."):
                continue
            child = relative / d
            paths.append(str(child).replace("\\", "/"))

    return sorted(set([p for p in paths if p and p != "."]))


def create_paths_on_disk(root_path, paths):
    root = Path(root_path)
    created_dirs = 0
    existing_dirs = 0
    created_files = 0
    existing_files = 0

    for rel in paths:
        target = root / Path(rel)

        if is_placeholder_file(rel):
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                existing_files += 1
            else:
                target.write_text("", encoding="utf-8")
                created_files += 1
        else:
            if target.exists():
                existing_dirs += 1
            else:
                target.mkdir(parents=True, exist_ok=True)
                created_dirs += 1

    return created_dirs, existing_dirs, created_files, existing_files


def build_template_paths(template_name, slug, date):
    if template_name not in TEMPLATES:
        raise Exception(f"Template inexistente: {template_name}")

    return [render_path(p, slug, date) for p in TEMPLATES[template_name]]


def build_paths_from_mode(mode, template_name, source_structure_path, manual_structure_text, slug, date):
    if mode == "Template interno":
        return build_template_paths(template_name, slug, date)

    if mode == "Copiar estrutura existente":
        if not str(source_structure_path or "").strip():
            raise Exception("Escolha uma pasta modelo.")
        return collect_folder_structure(source_structure_path)

    if mode == "Criar estrutura manual":
        paths = normalize_manual_lines(manual_structure_text)
        if not paths:
            raise Exception("A estrutura manual está vazia.")
        return paths

    raise Exception(f"Modo inválido: {mode}")


# ============================================================
# RESOLVE BINS
# ============================================================

def get_media_pool():
    if not resolve:
        raise Exception("DaVinci Resolve API não carregada.")

    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()

    if not project:
        raise Exception("Nenhum projeto aberto no DaVinci Resolve.")

    return project.GetMediaPool()


def safe_add_folder(media_pool, parent, name):
    subfolders = parent.GetSubFolders() or {}

    for _, folder in subfolders.items():
        try:
            if folder.GetName() == name:
                return folder, False
        except Exception:
            pass

    return media_pool.AddSubFolder(parent, name), True


def create_bins_from_paths(media_pool, project_bin_name, paths):
    root = media_pool.GetRootFolder()
    project_bin, project_created = safe_add_folder(media_pool, root, project_bin_name)

    created = {}
    created_count = 1 if project_created else 0
    existing_count = 0 if project_created else 1

    for rel in paths:
        if is_placeholder_file(rel):
            rel = str(Path(rel).parent)

        rel = str(rel).replace("\\", "/")
        parts = [p for p in rel.split("/") if p]

        if not parts:
            continue

        parent = project_bin
        current = ""

        for part in parts:
            current = f"{current}/{part}" if current else part

            if current in created:
                parent = created[current]
                continue

            folder, was_created = safe_add_folder(media_pool, parent, part)
            created[current] = folder
            parent = folder

            if was_created:
                created_count += 1
            else:
                existing_count += 1

    return created_count, existing_count


def rename_clips_in_current_folder(media_pool, slug):
    folder = media_pool.GetCurrentFolder()
    clips = folder.GetClips() or {}

    renamed = 0
    skipped = 0
    index = 1

    for _, clip in clips.items():
        try:
            props = clip.GetClipProperty() or {}
            file_name = props.get("File Name", "")
            ext = ""

            if "." in file_name:
                ext = "." + file_name.split(".")[-1].lower()

            new_name = f"{slug}_clip_{index:03d}{ext}"
            ok = clip.SetClipProperty("Clip Name", new_name)

            if ok:
                renamed += 1
            else:
                skipped += 1

        except Exception:
            skipped += 1

        index += 1

    return renamed, skipped


# ============================================================
# RENAME FÍSICO + ROLLBACK
# ============================================================

def scan_files(folder, include_all=False):
    folder = Path(folder)

    if not folder.exists():
        raise Exception("Pasta de arquivos não encontrada.")

    if not folder.is_dir():
        raise Exception("O caminho de rename não é uma pasta.")

    files = []

    for item in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_file():
            continue
        if item.name.startswith("."):
            continue
        if include_all or item.suffix.lower() in MEDIA_EXTS:
            files.append(item)

    return files


def apply_rename_rule(base_name, ext, index, opts):
    mode = opts.get("rename_mode")
    name = base_name

    if mode == "Add Before Name":
        name = f"{safe_name(opts.get('add_text'))}{name}"

    elif mode == "Add After Name":
        name = f"{name}{safe_name(opts.get('add_text'))}"

    elif mode == "Find and Replace":
        find_text = opts.get("find_text") or ""
        replace_text = opts.get("replace_text") or ""
        if find_text:
            name = name.replace(find_text, replace_text)

    elif mode == "Sequence":
        prefix = safe_name(opts.get("sequence_prefix") or "")
        start = int(opts.get("sequence_start") or 1)
        digits = int(opts.get("sequence_digits") or 3)
        name = f"{prefix}{str(start + index).zfill(digits)}"

    elif mode == "Project Slug + Sequence":
        slug = slugify(opts.get("project_title"))
        middle = safe_name(opts.get("sequence_prefix") or "clip")
        start = int(opts.get("sequence_start") or 1)
        digits = int(opts.get("sequence_digits") or 3)
        name = f"{slug}_{middle}_{str(start + index).zfill(digits)}"

    elif mode == "Replace Full Name":
        name = safe_name(opts.get("replace_full_name") or "")

    if opts.get("lowercase", True):
        name = name.lower()

    name = safe_name(name)

    final_ext = ext if opts.get("keep_extension", True) else ""
    return f"{name}{final_ext}"


def rename_preview(opts):
    files = scan_files(opts.get("rename_folder"), opts.get("include_all_files", False))
    seen = {}
    rows = []

    for i, file_path in enumerate(files):
        ext = file_path.suffix
        base = file_path.stem
        new_name = apply_rename_rule(base, ext, i, opts)
        new_path = file_path.parent / new_name

        status = "ok"
        if new_name == file_path.name:
            status = "unchanged"
        elif new_path.exists() and new_path != file_path:
            status = "conflict_exists"
        elif new_name in seen:
            status = "conflict_duplicate"

        seen[new_name] = True

        rows.append({
            "index": i + 1,
            "old_path": str(file_path),
            "new_path": str(new_path),
            "old_name": file_path.name,
            "new_name": new_name,
            "status": status
        })

    return rows


def apply_rename(opts):
    plan = rename_preview(opts)

    has_conflict = any(row["status"] in ("conflict_exists", "conflict_duplicate") for row in plan)

    if has_conflict:
        return {
            "blocked": True,
            "message": "Renomeação bloqueada: existem conflitos no preview.",
            "applied": plan,
            "rollback_path": None
        }

    applied = []

    for row in plan:
        if row["status"] != "ok":
            row["status"] = "unchanged" if row["status"] == "unchanged" else "skipped"
            applied.append(row)
            continue

        os.rename(row["old_path"], row["new_path"])
        row["status"] = "renamed"
        applied.append(row)

    folder = Path(opts.get("rename_folder"))
    rollback_path = folder / f".argo_rollback_{int(datetime.now().timestamp())}.json"

    rollback_path.write_text(
        json.dumps(applied, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return {
        "blocked": False,
        "message": "Renomeação aplicada.",
        "applied": applied,
        "rollback_path": str(rollback_path)
    }


def rollback_from_file(rollback_file):
    path = Path(rollback_file)

    if not path.exists():
        raise Exception("Arquivo de rollback não encontrado.")

    data = json.loads(path.read_text(encoding="utf-8"))
    restored = 0
    skipped = 0

    for row in reversed(data):
        if row.get("status") != "renamed":
            skipped += 1
            continue

        old_path = Path(row["old_path"])
        new_path = Path(row["new_path"])

        if new_path.exists() and not old_path.exists():
            os.rename(str(new_path), str(old_path))
            restored += 1
        else:
            skipped += 1

    return restored, skipped


def format_rename_table(rows, title="PREVIEW RENAME"):
    out = []
    out.append(title)
    out.append("")
    out.append(f"{'#':<4} {'ANTES':<42} {'DEPOIS':<42} STATUS")
    out.append("-" * 110)

    for row in rows:
        old_name = row["old_name"][:40]
        new_name = row["new_name"][:40]
        status = short_status(row["status"])
        out.append(f"{row['index']:<4} {old_name:<42} {new_name:<42} {status}")

    return "\n".join(out)


# ============================================================
# CORE
# ============================================================

def structure_preview(args):
    project_title = args["project_title"].strip()
    if not project_title:
        raise Exception("Informe o título do projeto.")

    date = validate_date(args["date"])
    slug = slugify(project_title)

    paths = build_paths_from_mode(
        args["mode"],
        args["template_name"],
        args["source_structure_path"],
        args["manual_structure_text"],
        slug,
        date
    )

    destination_root = Path(args["root_path"]) / slug

    output = []
    output.append(f"ARGO ORGANIZADOR {APP_VERSION} — PREVIEW")
    output.append("")
    output.append(f"Modo: {args['mode']}")
    output.append(f"Slug: {slug}")
    output.append(f"Destino final: {destination_root}")
    output.append(f"Itens: {len(paths)}")
    output.append("")
    output.append("Estrutura:")
    for i, p in enumerate(paths, 1):
        output.append(f"{i:03d}. {p}")

    return "\n".join(output)


def run_structure(args):
    project_title = args["project_title"].strip()

    if not project_title:
        raise Exception("Informe o título do projeto.")

    if not args["root_path"].strip():
        raise Exception("Informe a pasta raiz de destino.")

    date = validate_date(args["date"])
    slug = slugify(project_title)
    destination_root = Path(args["root_path"]) / slug

    paths = build_paths_from_mode(
        args["mode"],
        args["template_name"],
        args["source_structure_path"],
        args["manual_structure_text"],
        slug,
        date
    )

    log = []
    log.append(f"ARGO ORGANIZADOR {APP_VERSION}")
    log.append("")
    log.append(f"Modo: {args['mode']}")
    log.append(f"Projeto: {project_title}")
    log.append(f"Slug: {slug}")
    log.append(f"Destino: {destination_root}")
    log.append(f"Data: {date}")
    log.append(f"Itens na estrutura: {len(paths)}")

    if args["create_disk"]:
        created_dirs, existing_dirs, created_files, existing_files = create_paths_on_disk(destination_root, paths)
        log.append("")
        log.append("DISCO")
        log.append(f"Pastas criadas: {created_dirs}")
        log.append(f"Pastas já existentes: {existing_dirs}")
        log.append(f"Arquivos placeholder criados: {created_files}")
        log.append(f"Arquivos placeholder já existentes: {existing_files}")

    if args["create_bins"] or args["rename_resolve_clips"]:
        media_pool = get_media_pool()

        if args["create_bins"]:
            created_bins, existing_bins = create_bins_from_paths(media_pool, slug, paths)
            log.append("")
            log.append("RESOLVE")
            log.append(f"Bins criados: {created_bins}")
            log.append(f"Bins já existentes: {existing_bins}")

        if args["rename_resolve_clips"]:
            renamed, skipped = rename_clips_in_current_folder(media_pool, slug)
            log.append("")
            log.append("RENOMEAÇÃO DE CLIPS DO BIN ATUAL")
            log.append(f"Clips renomeados: {renamed}")
            log.append(f"Clips ignorados/falhados: {skipped}")

    log.append("")
    log.append("Concluído.")
    return "\n".join(log)


# ============================================================
# UI
# ============================================================

def request_dir_safe(fusion):
    try:
        selected = fusion.RequestDir()
        return selected if selected else ""
    except Exception:
        return ""


def request_file_safe(fusion):
    try:
        selected = fusion.RequestFile()
        return selected if selected else ""
    except Exception:
        return ""


def build_ui():
    fusion = resolve.Fusion()
    ui = fusion.UIManager
    dispatcher = bmd.UIDispatcher(ui)

    template_names = list(TEMPLATES.keys())

    modes = [
        "Template interno",
        "Copiar estrutura existente",
        "Criar estrutura manual"
    ]

    rename_modes = [
        "Add Before Name",
        "Add After Name",
        "Find and Replace",
        "Sequence",
        "Project Slug + Sequence",
        "Replace Full Name"
    ]

    win = dispatcher.AddWindow({
        "ID": "ArgoOrganizadorWindow",
        "WindowTitle": f"Argo Organizador {APP_VERSION}",
        "Geometry": [160, 80, 980, 860],
    }, [
        ui.VGroup({"Spacing": 8, "Weight": 1}, [

            ui.Label({
                "Text": f"Argo Organizador {APP_VERSION} — Resolve + Finder-style Rename + Rollback"
            }),

            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Título:", "Weight": 0}),
                ui.LineEdit({"ID": "ProjectTitle", "Text": DEFAULT_PROJECT_TITLE, "Weight": 1})
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Destino raiz:", "Weight": 0}),
                ui.LineEdit({"ID": "RootPath", "Text": DEFAULT_ROOT, "Weight": 1}),
                ui.Button({"ID": "BrowseRootButton", "Text": "ESCOLHER..."})
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Data YYYYMMDD:", "Weight": 0}),
                ui.LineEdit({"ID": "DateField", "Text": DEFAULT_DATE, "Weight": 1})
            ]),

            ui.Label({"Text": "Modo de estrutura:"}),
            ui.ComboBox({"ID": "ModeCombo"}),

            ui.Label({"Text": "Template interno:"}),
            ui.ComboBox({"ID": "TemplateCombo"}),

            ui.Label({"Text": "Pasta modelo existente — usada no modo Copiar estrutura existente:"}),
            ui.HGroup({"Spacing": 6}, [
                ui.LineEdit({"ID": "SourceStructurePath", "Text": "", "PlaceholderText": "/Volumes/Projeto_Modelo", "Weight": 1}),
                ui.Button({"ID": "BrowseSourceButton", "Text": "ESCOLHER..."})
            ]),

            ui.Label({"Text": "Estrutura manual — uma pasta por linha:"}),
            ui.TextEdit({"ID": "ManualStructure", "PlainText": DEFAULT_MANUAL_STRUCTURE, "Weight": 1}),

            ui.HGroup({"Spacing": 12}, [
                ui.CheckBox({"ID": "CreateDisk", "Text": "Criar pastas no disco", "Checked": True}),
                ui.CheckBox({"ID": "CreateBins", "Text": "Criar bins no Resolve", "Checked": True}),
                ui.CheckBox({"ID": "RenameResolveClips", "Text": "Renomear clips do bin atual", "Checked": False})
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Button({"ID": "PreviewStructureButton", "Text": "PREVIEW ESTRUTURA"}),
                ui.Button({"ID": "ApplyStructureButton", "Text": "APLICAR ESTRUTURA"})
            ]),

            ui.Label({"Text": "Renomear arquivos físicos — estilo Finder/Renamer:"}),

            ui.HGroup({"Spacing": 6}, [
                ui.LineEdit({"ID": "RenameFolder", "Text": "", "PlaceholderText": "/Volumes/Projeto/Media", "Weight": 1}),
                ui.Button({"ID": "BrowseRenameFolderButton", "Text": "ESCOLHER..."})
            ]),

            ui.Label({"Text": "Regra de rename:"}),
            ui.ComboBox({"ID": "RenameModeCombo"}),

            ui.HGroup({"Spacing": 8}, [
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Texto para Add Before / Add After:"}),
                    ui.LineEdit({"ID": "AddText", "Text": "cabρα_"})
                ]),
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Find:"}),
                    ui.LineEdit({"ID": "FindText", "Text": ""})
                ]),
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Replace:"}),
                    ui.LineEdit({"ID": "ReplaceText", "Text": ""})
                ])
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Replace Full Name:"}),
                    ui.LineEdit({"ID": "ReplaceFullName", "Text": ""})
                ]),
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Sequence Prefix:"}),
                    ui.LineEdit({"ID": "SequencePrefix", "Text": "clip"})
                ]),
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Start:"}),
                    ui.LineEdit({"ID": "SequenceStart", "Text": "1"})
                ]),
                ui.VGroup({"Weight": 1}, [
                    ui.Label({"Text": "Digits:"}),
                    ui.LineEdit({"ID": "SequenceDigits", "Text": "3"})
                ])
            ]),

            ui.HGroup({"Spacing": 12}, [
                ui.CheckBox({"ID": "Lowercase", "Text": "Converter para minúsculas", "Checked": True}),
                ui.CheckBox({"ID": "KeepExtension", "Text": "Manter extensão", "Checked": True}),
                ui.CheckBox({"ID": "IncludeAllFiles", "Text": "Incluir todos os arquivos", "Checked": False})
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Button({"ID": "PreviewRenameButton", "Text": "PREVIEW RENAME"}),
                ui.Button({"ID": "ApplyRenameButton", "Text": "APLICAR RENAME"})
            ]),

            ui.Label({"Text": "Rollback:"}),
            ui.HGroup({"Spacing": 6}, [
                ui.LineEdit({"ID": "RollbackFile", "Text": "", "PlaceholderText": ".argo_rollback_*.json", "Weight": 1}),
                ui.Button({"ID": "BrowseRollbackButton", "Text": "ESCOLHER..."})
            ]),

            ui.Button({"ID": "RunRollbackButton", "Text": "EXECUTAR ROLLBACK"}),

            ui.Label({"Text": "Log / Preview:"}),
            ui.TextEdit({"ID": "LogOutput", "ReadOnly": True, "PlainText": "Pronto.", "Weight": 2})
        ])
    ])

    itm = win.GetItems()

    for mode in modes:
        itm["ModeCombo"].AddItem(mode)

    for name in template_names:
        itm["TemplateCombo"].AddItem(name)

    for mode in rename_modes:
        itm["RenameModeCombo"].AddItem(mode)

    try:
        itm["TemplateCombo"].CurrentIndex = template_names.index("Cinemateca_Deposito_Legal_Cinema")
    except ValueError:
        itm["TemplateCombo"].CurrentIndex = 0

    itm["ModeCombo"].CurrentIndex = 0
    itm["RenameModeCombo"].CurrentIndex = 0

    def collect_structure_args():
        return {
            "mode": itm["ModeCombo"].CurrentText,
            "project_title": itm["ProjectTitle"].Text,
            "root_path": itm["RootPath"].Text,
            "template_name": itm["TemplateCombo"].CurrentText,
            "source_structure_path": itm["SourceStructurePath"].Text,
            "manual_structure_text": itm["ManualStructure"].PlainText,
            "date": itm["DateField"].Text,
            "create_disk": itm["CreateDisk"].Checked,
            "create_bins": itm["CreateBins"].Checked,
            "rename_resolve_clips": itm["RenameResolveClips"].Checked
        }

    def collect_rename_args():
        return {
            "project_title": itm["ProjectTitle"].Text,
            "rename_folder": itm["RenameFolder"].Text,
            "rename_mode": itm["RenameModeCombo"].CurrentText,
            "add_text": itm["AddText"].Text,
            "find_text": itm["FindText"].Text,
            "replace_text": itm["ReplaceText"].Text,
            "replace_full_name": itm["ReplaceFullName"].Text,
            "sequence_prefix": itm["SequencePrefix"].Text,
            "sequence_start": itm["SequenceStart"].Text,
            "sequence_digits": itm["SequenceDigits"].Text,
            "lowercase": itm["Lowercase"].Checked,
            "keep_extension": itm["KeepExtension"].Checked,
            "include_all_files": itm["IncludeAllFiles"].Checked
        }

    def on_browse_root(ev):
        selected = request_dir_safe(fusion)
        if selected:
            itm["RootPath"].Text = selected

    def on_browse_source(ev):
        selected = request_dir_safe(fusion)
        if selected:
            itm["SourceStructurePath"].Text = selected
            itm["ModeCombo"].CurrentIndex = 1

    def on_browse_rename_folder(ev):
        selected = request_dir_safe(fusion)
        if selected:
            itm["RenameFolder"].Text = selected

    def on_browse_rollback(ev):
        selected = request_file_safe(fusion)
        if selected:
            itm["RollbackFile"].Text = selected

    def on_preview_structure(ev):
        try:
            itm["LogOutput"].PlainText = structure_preview(collect_structure_args())
        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO NO PREVIEW DE ESTRUTURA:\n{str(e)}"

    def on_apply_structure(ev):
        try:
            itm["LogOutput"].PlainText = run_structure(collect_structure_args())
        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO AO APLICAR ESTRUTURA:\n{str(e)}"

    def on_preview_rename(ev):
        try:
            rows = rename_preview(collect_rename_args())
            itm["LogOutput"].PlainText = format_rename_table(rows, "PREVIEW RENAME — nada foi renomeado")
        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO NO PREVIEW RENAME:\n{str(e)}"

    def on_apply_rename(ev):
        try:
            result = apply_rename(collect_rename_args())
            title = result["message"]
            if result.get("rollback_path"):
                title += f"\nRollback salvo em: {result['rollback_path']}"
            itm["LogOutput"].PlainText = format_rename_table(result["applied"], title)
        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO AO APLICAR RENAME:\n{str(e)}"

    def on_run_rollback(ev):
        try:
            restored, skipped = rollback_from_file(itm["RollbackFile"].Text)
            itm["LogOutput"].PlainText = (
                "ROLLBACK CONCLUÍDO\n\n"
                f"Arquivos restaurados: {restored}\n"
                f"Ignorados/falhados: {skipped}"
            )
        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO NO ROLLBACK:\n{str(e)}"

    def on_close(ev):
        dispatcher.ExitLoop()

    win.On.BrowseRootButton.Clicked = on_browse_root
    win.On.BrowseSourceButton.Clicked = on_browse_source
    win.On.BrowseRenameFolderButton.Clicked = on_browse_rename_folder
    win.On.BrowseRollbackButton.Clicked = on_browse_rollback

    win.On.PreviewStructureButton.Clicked = on_preview_structure
    win.On.ApplyStructureButton.Clicked = on_apply_structure
    win.On.PreviewRenameButton.Clicked = on_preview_rename
    win.On.ApplyRenameButton.Clicked = on_apply_rename
    win.On.RunRollbackButton.Clicked = on_run_rollback

    win.On.ArgoOrganizadorWindow.Close = on_close

    win.Show()
    dispatcher.RunLoop()
    win.Hide()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    if not resolve:
        print("ERRO: DaVinci Resolve API não carregada.")
    else:
        build_ui()
