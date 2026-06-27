import csv, os

CSV_PATH = "/Users/argomini/Documents/Claude/Projects/PassadoPresente Documentario/markers.csv"
FPS = 23.976

CAT_COLOR = {
    "memoria":"Blue","memória":"Blue",
    "trauma":"Red",
    "tensao":"Orange","tensão":"Orange",
    "identidade":"Purple",
    "ensaio":"Green",
}

def tc_to_frames(tc):
    h,m,s,f = map(int,tc.strip().split(":"))
    return int((h*3600+m*60+s)*FPS+f)

def get_all_clips(folder, out={}):
    for item in (folder.GetClipList() or []):
        stem = os.path.splitext(item.GetName())[0].replace("20200101_","")
        out[stem.lower()] = item
    for sub in (folder.GetSubFolderList() or []):
        get_all_clips(sub, out)
    return out

resolve  = bmd.scriptapp("Resolve")
project  = resolve.GetProjectManager().GetCurrentProject()
mp       = project.GetMediaPool()
clips    = get_all_clips(mp.GetRootFolder())
print(f"{len(clips)} clips no pool")

grouped = {}
with open(CSV_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        key = row["Source"].strip().replace("_markers","").replace("20200101_","")
        grouped.setdefault(key,[]).append(row)

ok = skipped = total = 0
for src, markers in sorted(grouped.items()):
    clip = clips.get(src.lower())
    if not clip:
        print(f"  NF  {src}"); skipped+=1; continue
    for m in clip.GetMarkers() or []:
        clip.DeleteMarkerAtFrame(m)
    added = 0
    for m in markers:
        cat  = m["Category"].strip().lower()
        fin  = tc_to_frames(m["Start"])
        dur  = max(1, tc_to_frames(m["End"])-fin)
        if clip.AddMarker(fin, CAT_COLOR.get(cat,"White"), m["Name"], m["Notes"], dur, ""):
            added+=1
    print(f"  OK  {src}  {added}/{len(markers)}")
    ok+=1; total+=added

print(f"\n{ok} clips  |  {total} markers  |  {skipped} não encontrados")
