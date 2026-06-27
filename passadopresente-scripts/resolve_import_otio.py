"""
resolve_import_otio.py
────────────────────────────────────────────────────────────────
Importa as timelines OTIO geradas pelo argo_otio.py diretamente
no DaVinci Resolve em execução, com mídia já linkada.

COMO USAR:
  1. Abra o DaVinci Resolve
  2. Abra (ou crie) o projeto desejado
  3. No terminal:
       python3 resolve_import_otio.py

REQUISITO: DaVinci Resolve 17+ com scripting habilitado.
  Resolve → Preferences → General → Enable Scripting API  ✓
────────────────────────────────────────────────────────────────
"""

import sys
import os

# ── Conecta ao Resolve ────────────────────────────────────────
RESOLVE_SCRIPT_API = (
    "/Library/Application Support/Blackmagic Design/"
    "DaVinci Resolve/Developer/Scripting/Modules"
)

if RESOLVE_SCRIPT_API not in sys.path:
    sys.path.append(RESOLVE_SCRIPT_API)

try:
    import DaVinciResolveScript as dvr
except ModuleNotFoundError:
    sys.exit(
        "✗ Módulo DaVinciResolveScript não encontrado.\n"
        "  Verifique se o DaVinci Resolve está aberto e que\n"
        "  o caminho da API está correto:\n"
        f"  {RESOLVE_SCRIPT_API}"
    )

resolve = dvr.scriptapp("Resolve")
if not resolve:
    sys.exit("✗ Não foi possível conectar ao DaVinci Resolve. Está aberto?")

project = resolve.GetProjectManager().GetCurrentProject()
if not project:
    sys.exit("✗ Nenhum projeto aberto no Resolve.")

media_pool = project.GetMediaPool()
print(f"✓ Conectado → projeto: {project.GetName()}\n")

# ── Timelines a importar ──────────────────────────────────────
OTIO_DIR = os.path.dirname(os.path.abspath(__file__))

TIMELINES = [
    "timeline_memoria.otio",
    "timeline_trauma.otio",
    "timeline_tensao.otio",
    "timeline_identidade.otio",
    "timeline_ensaio.otio",
]

# ── Importa cada timeline ─────────────────────────────────────
ok   = []
fail = []

for fname in TIMELINES:
    path = os.path.join(OTIO_DIR, fname)

    if not os.path.exists(path):
        print(f"  ⚠  não encontrado: {fname}")
        fail.append(fname)
        continue

    result = media_pool.ImportTimelineFromFile(path)
    if result:
        print(f"  ✓  {fname}")
        ok.append(fname)
    else:
        print(f"  ✗  falhou: {fname}")
        fail.append(fname)

# ── Resumo ────────────────────────────────────────────────────
print(f"\n{len(ok)} importadas  |  {len(fail)} com problema")
if fail:
    print("  Arquivos com problema:", ", ".join(fail))
