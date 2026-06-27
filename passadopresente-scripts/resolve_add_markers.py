"""
resolve_add_markers.py
────────────────────────────────────────────────────────────────
Lê markers.csv e adiciona markers coloridos nos clips do
Media Pool do DaVinci Resolve em execução.

Cada marker recebe:
  • Cor      → categoria (memoria=Azul, trauma=Vermelho, etc.)
  • Nome     → campo Name do CSV
  • Note     → campo Notes do CSV
  • Duração  → calculada pelos TC In/Out

COMO USAR:
  1. Abra o DaVinci Resolve com o projeto aberto
  2. Workspace → Scripts → Utility → resolve_add_markers
────────────────────────────────────────────────────────────────
"""

import sys, os, csv

# ── API do Resolve ────────────────────────────────────────────
# Quando o script roda via Workspace → Scripts, 'bmd' já está disponível
try:
    resolve = bmd.scriptapp("Resolve")          # dentro do Resolve
except NameError:
    # fallback: execução externa via terminal
    sys.path.append(
        "/Library/Application Support/Blackmagic Design/"
        "DaVinci Resolve/Developer/Scripting/Modules"
    )
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")

if not resolve:
    sys.exit("✗ Não conectou ao Resolve.")

project    = resolve.GetProjectManager().GetCurrentProject()
media_pool = project.GetMediaPool()
root_bin   = media_pool.GetRootFolder()

print(f"✓ Projeto: {project.GetName()}\n")

# ── Configurações ─────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markers.csv")
FPS      = 23.976

# Cores DaVinci por categoria
CAT_COLOR = {
    "memoria":    "Blue",
    "memória":    "Blue",
    "trauma":     "Red",
    "tensao":     "Orange",
    "tensão":     "Orange",
    "identidade": "Purple",
    "ensaio":     "Green",
}

# ── Converte TC → frames absolutos ───────────────────────────
def tc_to_frames(tc):
    hh, mm, ss, ff = map(int, tc.strip().split(":"))
    return int((hh*3600 + mm*60 + ss) * FPS + ff)

# ── Indexa clips do Media Pool ────────────────────────────────
def get_all_clips(folder):
    clips = {}
    for item in (folder.GetClipList() or []):
        name = item.GetName()
        stem = os.path.splitext(name)[0]           # sem extensão
        stem_clean = stem.replace("20200101_","")  # remove prefixo
        clips[stem_clean.lower()] = item
        clips[stem.lower()] = item
    for subfolder in (folder.GetSubFolderList() or []):
        clips.update(get_all_clips(subfolder))
    return clips

print("Indexando clips do Media Pool…")
pool_clips = get_all_clips(root_bin)
print(f"  {len(pool_clips)} clips encontrados\n")

# ── Lê CSV e agrupa por source ────────────────────────────────
grouped = {}
with open(CSV_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = row["Source"].strip().replace("_markers","").replace("20200101_","")
        grouped.setdefault(key, []).append(row)

# ── Adiciona markers ──────────────────────────────────────────
ok_clips   = 0
ok_markers = 0
skipped    = []

for source_key, markers in sorted(grouped.items()):
    clip = pool_clips.get(source_key.lower())
    if not clip:
        skipped.append(source_key)
        continue

    # Remove markers existentes (opcional — comentar para manter)
    existing = clip.GetMarkers()
    if existing:
        for frame_id in list(existing.keys()):
            clip.DeleteMarkerAtFrame(frame_id)

    added = 0
    for m in markers:
        cat_raw  = m["Category"].strip().lower()
        color    = CAT_COLOR.get(cat_raw, "White")
        name     = m["Name"].strip()
        note     = m["Notes"].strip()
        frame_in = tc_to_frames(m["Start"])
        dur      = max(1, tc_to_frames(m["End"]) - frame_in)

        result = clip.AddMarker(frame_in, color, name, note, dur, "")
        if result:
            added += 1

    print(f"  ✓  {source_key:20s}  {added}/{len(markers)} markers")
    ok_clips   += 1
    ok_markers += added

# ── Resumo ────────────────────────────────────────────────────
print(f"\n{'─'*50}")
print(f"  Clips atualizados : {ok_clips}")
print(f"  Markers adicionados: {ok_markers}")

if skipped:
    print(f"\n  ⚠  {len(skipped)} clips não encontrados no Media Pool:")
    for s in skipped:
        print(f"      {s}")
