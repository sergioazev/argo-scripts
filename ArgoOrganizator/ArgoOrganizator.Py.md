---
type: note
domain: unclassified
date: 2026-05-24
status: work-in-progress
---
![[ArgoOrganizador.py]]


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArgoOrganizador.py V4
DaVinci Resolve > Workspace > Scripts > Utility > ArgoOrganizador

Recursos:
- Templates técnicos embutidos
- Copiar estrutura existente com botão ESCOLHER...
- Criar estrutura manual
- Preview antes de aplicar
- Criar pastas no disco
- Criar bins no Resolve
- Renomear clips do bin atual
"""

import os
import re
import unicodedata
from pathlib import Path
from datetime import datetime


DEFAULT_PROJECT_TITLE = "O Cabra Marcado Para Morrer"
DEFAULT_ROOT = str(Path.home() / "Movies" / "ARGO_ORGANIZADOR")
DEFAULT_DATE = datetime.now().strftime("%Y%m%d")
REMOVE_INITIAL_ARTICLES = True


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
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r01",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r01/checksum.txt.placeholder",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r02",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r02/checksum.txt.placeholder",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r03",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r03/checksum.txt.placeholder",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r04",
        "{slug}_dcdm_16b_sdr_xyz_g26_{date}_239_4096x1716/r04/checksum.txt.placeholder"
    ],

    "Netflix_IMF_Delivery": [
        "{slug}_imf_delivery",
        "{slug}_imf_delivery/ASSETMAP",
        "{slug}_imf_delivery/PKL",
        "{slug}_imf_delivery/CPL",
        "{slug}_imf_delivery/OPL_optional",
        "{slug}_imf_delivery/MXF",
        "{slug}_imf_delivery/QC",
        "{slug}_imf_delivery/QC/reports"
    ],

    "DCP_SMPTE_DCI_Package": [
        "{slug}_dcp_smpte",
        "{slug}_dcp_smpte/CPL",
        "{slug}_dcp_smpte/PKL",
        "{slug}_dcp_smpte/ASSETMAP",
        "{slug}_dcp_smpte/VOLINDEX",
        "{slug}_dcp_smpte/MXF",
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


def slugify(text):
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    if REMOVE_INITIAL_ARTICLES:
        text = re.sub(r"^(a|o|as|os)\s+", "", text)

    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def validate_date(date_text):
    if not re.match(r"^\d{8}$", date_text):
        raise Exception("Data inválida. Use formato YYYYMMDD, exemplo: 20260501.")
    return date_text


def render_path(path_template, slug, date):
    return path_template.replace("{slug}", slug).replace("{date}", date)


def is_placeholder_file(path):
    name = Path(path).name.lower()
    return name.endswith(".placeholder") or name == "checksum.txt"


def normalize_manual_lines(text):
    lines = []

    for line in text.splitlines():
        clean = line.strip().strip("/").strip()

        if not clean:
            continue

        if clean.startswith("#"):
            continue

        clean = clean.replace("\\", "/")
        lines.append(clean)

    return sorted(set(lines))


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

        if is_placeholder_file(target):
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

        rel = rel.replace("\\", "/")
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


def build_template_paths(template_name, slug, date):
    if template_name not in TEMPLATES:
        raise Exception(f"Template inexistente: {template_name}")

    return [render_path(p, slug, date) for p in TEMPLATES[template_name]]


def build_paths_from_mode(mode, template_name, source_structure_path, manual_structure_text, slug, date):
    if mode == "Template interno":
        return build_template_paths(template_name, slug, date)

    if mode == "Copiar estrutura existente":
        if not source_structure_path.strip():
            raise Exception("Escolha uma pasta modelo no modo Copiar estrutura existente.")
        return collect_folder_structure(source_structure_path)

    if mode == "Criar estrutura manual":
        paths = normalize_manual_lines(manual_structure_text)
        if not paths:
            raise Exception("A estrutura manual está vazia.")
        return paths

    raise Exception(f"Modo inválido: {mode}")


def run_organizer(
    mode,
    project_title,
    root_path,
    template_name,
    source_structure_path,
    manual_structure_text,
    date,
    create_disk,
    create_bins,
    rename_clips
):
    project_title = project_title.strip()

    if not project_title:
        raise Exception("Informe o título do projeto.")

    if not root_path.strip():
        raise Exception("Informe a pasta raiz de destino.")

    date = validate_date(date)
    slug = slugify(project_title)
    destination_root = Path(root_path) / slug

    paths = build_paths_from_mode(
        mode,
        template_name,
        source_structure_path,
        manual_structure_text,
        slug,
        date
    )

    log = []
    log.append("ARGO ORGANIZADOR V4")
    log.append("")
    log.append(f"Modo: {mode}")
    log.append(f"Projeto: {project_title}")
    log.append(f"Slug: {slug}")
    log.append(f"Destino: {destination_root}")
    log.append(f"Data: {date}")

    if mode == "Template interno":
        log.append(f"Template: {template_name}")

    if mode == "Copiar estrutura existente":
        log.append(f"Modelo copiado de: {source_structure_path}")

    log.append("")
    log.append(f"Itens na estrutura: {len(paths)}")

    if create_disk:
        created_dirs, existing_dirs, created_files, existing_files = create_paths_on_disk(destination_root, paths)
        log.append("")
        log.append("DISCO")
        log.append(f"Pastas criadas: {created_dirs}")
        log.append(f"Pastas já existentes: {existing_dirs}")
        log.append(f"Arquivos placeholder criados: {created_files}")
        log.append(f"Arquivos placeholder já existentes: {existing_files}")

    if create_bins or rename_clips:
        media_pool = get_media_pool()

        if create_bins:
            created_bins, existing_bins = create_bins_from_paths(media_pool, slug, paths)
            log.append("")
            log.append("RESOLVE")
            log.append(f"Bins criados: {created_bins}")
            log.append(f"Bins já existentes: {existing_bins}")

        if rename_clips:
            renamed, skipped = rename_clips_in_current_folder(media_pool, slug)
            log.append("")
            log.append("RENOMEAÇÃO")
            log.append(f"Clips renomeados no bin atual: {renamed}")
            log.append(f"Clips ignorados/falhados: {skipped}")

    log.append("")
    log.append("Concluído.")

    return "\n".join(log)


def build_preview(
    mode,
    project_title,
    root_path,
    template_name,
    source_structure_path,
    manual_structure_text,
    date
):
    project_title = project_title.strip()

    if not project_title:
        raise Exception("Informe o título do projeto.")

    date = validate_date(date)
    slug = slugify(project_title)

    paths = build_paths_from_mode(
        mode,
        template_name,
        source_structure_path,
        manual_structure_text,
        slug,
        date
    )

    destination_root = Path(root_path) / slug

    output = []
    output.append("PREVIEW — nada foi criado")
    output.append("")
    output.append(f"Modo: {mode}")
    output.append(f"Slug: {slug}")
    output.append(f"Destino final: {destination_root}")
    output.append(f"Itens: {len(paths)}")
    output.append("")
    output.append("Estrutura:")
    output.extend(paths)

    return "\n".join(output)


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

    win = dispatcher.AddWindow({
        "ID": "ArgoOrganizadorWindow",
        "WindowTitle": "Argo Organizador V4",
        "Geometry": [220, 100, 820, 760],
    }, [
        ui.VGroup({"Spacing": 8, "Weight": 1}, [

            ui.Label({
                "Text": "Argo Organizador V4 — Templates, cópia por Finder e estrutura manual"
            }),

            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Título:", "Weight": 0}),
                ui.LineEdit({
                    "ID": "ProjectTitle",
                    "Text": DEFAULT_PROJECT_TITLE,
                    "Weight": 1
                })
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Destino raiz:", "Weight": 0}),
                ui.LineEdit({
                    "ID": "RootPath",
                    "Text": DEFAULT_ROOT,
                    "Weight": 1
                }),
                ui.Button({
                    "ID": "BrowseRootButton",
                    "Text": "ESCOLHER..."
                })
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Label({"Text": "Data YYYYMMDD:", "Weight": 0}),
                ui.LineEdit({
                    "ID": "DateField",
                    "Text": DEFAULT_DATE,
                    "Weight": 1
                })
            ]),

            ui.Label({"Text": "Modo:"}),
            ui.ComboBox({"ID": "ModeCombo"}),

            ui.Label({"Text": "Template interno:"}),
            ui.ComboBox({"ID": "TemplateCombo"}),

            ui.Label({"Text": "Pasta modelo existente — usada no modo Copiar estrutura existente:"}),

            ui.HGroup({"Spacing": 6}, [
                ui.LineEdit({
                    "ID": "SourceStructurePath",
                    "Text": "",
                    "PlaceholderText": "/Volumes/Projeto_Modelo",
                    "Weight": 1
                }),
                ui.Button({
                    "ID": "BrowseSourceButton",
                    "Text": "ESCOLHER..."
                })
            ]),

            ui.Label({"Text": "Estrutura manual — uma pasta por linha:"}),
            ui.TextEdit({
                "ID": "ManualStructure",
                "PlainText": DEFAULT_MANUAL_STRUCTURE,
                "Weight": 2
            }),

            ui.HGroup({"Spacing": 12}, [
                ui.CheckBox({
                    "ID": "CreateDisk",
                    "Text": "Criar pastas no disco",
                    "Checked": True
                }),
                ui.CheckBox({
                    "ID": "CreateBins",
                    "Text": "Criar bins no Resolve",
                    "Checked": True
                }),
                ui.CheckBox({
                    "ID": "RenameClips",
                    "Text": "Renomear clips do bin atual",
                    "Checked": False
                })
            ]),

            ui.HGroup({"Spacing": 8}, [
                ui.Button({
                    "ID": "PreviewButton",
                    "Text": "PREVIEW"
                }),
                ui.Button({
                    "ID": "ApplyButton",
                    "Text": "APLICAR"
                }),
                ui.Button({
                    "ID": "CloseButton",
                    "Text": "FECHAR"
                })
            ]),

            ui.Label({"Text": "Log:"}),
            ui.TextEdit({
                "ID": "LogOutput",
                "ReadOnly": True,
                "PlainText": "Pronto.",
                "Weight": 2
            })
        ])
    ])

    itm = win.GetItems()

    for mode in modes:
        itm["ModeCombo"].AddItem(mode)

    for name in template_names:
        itm["TemplateCombo"].AddItem(name)

    try:
        itm["TemplateCombo"].CurrentIndex = template_names.index("Cinemateca_Deposito_Legal_Cinema")
    except ValueError:
        itm["TemplateCombo"].CurrentIndex = 0

    itm["ModeCombo"].CurrentIndex = 0

    def collect_inputs():
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
            "rename_clips": itm["RenameClips"].Checked
        }

    def request_dir_safe():
        try:
            selected = fusion.RequestDir()
            return selected if selected else ""
        except Exception:
            return ""

    def on_browse_root(ev):
        selected = request_dir_safe()
        if selected:
            itm["RootPath"].Text = selected

    def on_browse_source(ev):
        selected = request_dir_safe()
        if selected:
            itm["SourceStructurePath"].Text = selected
            itm["ModeCombo"].CurrentIndex = 1

    def on_preview(ev):
        try:
            args = collect_inputs()
            result = build_preview(
                mode=args["mode"],
                project_title=args["project_title"],
                root_path=args["root_path"],
                template_name=args["template_name"],
                source_structure_path=args["source_structure_path"],
                manual_structure_text=args["manual_structure_text"],
                date=args["date"]
            )
            itm["LogOutput"].PlainText = result

        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO NO PREVIEW:\n{str(e)}"

    def on_apply(ev):
        try:
            args = collect_inputs()
            result = run_organizer(**args)
            itm["LogOutput"].PlainText = result

        except Exception as e:
            itm["LogOutput"].PlainText = f"ERRO:\n{str(e)}"

    def on_close(ev):
        dispatcher.ExitLoop()

    win.On.BrowseRootButton.Clicked = on_browse_root
    win.On.BrowseSourceButton.Clicked = on_browse_source
    win.On.PreviewButton.Clicked = on_preview
    win.On.ApplyButton.Clicked = on_apply
    win.On.CloseButton.Clicked = on_close
    win.On.ArgoOrganizadorWindow.Close = on_close

    win.Show()
    dispatcher.RunLoop()
    win.Hide()


if __name__ == "__main__":
    if not resolve:
        print("ERRO: DaVinci Resolve API não carregada.")
    else:
        build_ui()

