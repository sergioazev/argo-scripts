import argparse
import csv
import os
import opentimelineio as otio

FPS = 23.976

# Bash mount root → Mac path visible to DaVinci
BASH_ROOT = "/sessions/practical-trusting-goodall/mnt/01_ORIGINALS"
MAC_ROOT  = "/Volumes/MEDIA5/PassadoPresente/01_ORIGINALS"

def build_file_index(originals_root):
    """Index all media files by lowercase stem → absolute bash path."""
    index = {}
    for dirpath, _, filenames in os.walk(originals_root):
        for fn in filenames:
            if fn.startswith("._") or fn.startswith("."):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in (".mov", ".mp4", ".mts", ".mxf"):
                continue
            stem = os.path.splitext(fn)[0].lower()
            full = os.path.join(dirpath, fn)
            # Keep first match (avoids __MACOSX duplicates)
            if stem not in index:
                index[stem] = full
    return index

def bash_to_mac(bash_path):
    return bash_path.replace(BASH_ROOT, MAC_ROOT, 1)

def tc_to_frames(tc):
    hh, mm, ss, ff = map(int, tc.split(":"))
    return int((hh * 3600 + mm * 60 + ss) * FPS + ff)

def make_clip(row, file_index):
    start    = tc_to_frames(row["Start"])
    end      = tc_to_frames(row["End"])
    duration = end - start

    sr = otio.opentime.TimeRange(
        start_time=otio.opentime.RationalTime(start, FPS),
        duration=otio.opentime.RationalTime(duration, FPS)
    )

    # Resolve media reference
    source_stem = row["Source"].strip().replace("_markers", "").lower()
    bash_path   = file_index.get(source_stem)

    if bash_path:
        mac_path  = bash_to_mac(bash_path)
        media_ref = otio.schema.ExternalReference(
            target_url="file://" + mac_path,
            available_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, FPS),
                duration=otio.opentime.RationalTime(end, FPS)
            )
        )
    else:
        media_ref = otio.schema.MissingReference()

    return otio.schema.Clip(
        name=row["Name"],
        media_reference=media_ref,
        source_range=sr
    )

def build_per_category(csv_path, file_index):
    CATEGORIES = ["memoria", "trauma", "tensao", "identidade", "ensaio"]
    NORMALISE  = {
        "memória": "memoria", "memoria": "memoria",
        "trauma":  "trauma",
        "tensão":  "tensao",  "tensao":  "tensao",
        "identidade": "identidade",
        "ensaio":  "ensaio",
    }

    grouped = {k: [] for k in CATEGORIES}
    missing = set()

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = NORMALISE.get(row["Category"].strip().lower())
            if key:
                grouped[key].append(row)
                stem = row["Source"].strip().replace("_markers", "").lower()
                if stem not in file_index:
                    missing.add(stem)

    out_dir   = os.path.dirname(os.path.abspath(csv_path))
    generated = []

    for cat in CATEGORIES:
        rows = grouped[cat]
        if not rows:
            continue

        timeline = otio.schema.Timeline(name=cat.upper())

        v_track = otio.schema.Track(name="V1 – " + cat, kind=otio.schema.TrackKind.Video)
        a_track = otio.schema.Track(name="A1 – " + cat, kind=otio.schema.TrackKind.Audio)

        for row in rows:
            clip = make_clip(row, file_index)
            v_track.append(clip)
            # Audio clip mirrors video (same ref, same range)
            a_track.append(make_clip(row, file_index))

        timeline.tracks.append(v_track)
        timeline.tracks.append(a_track)

        out_path = os.path.join(out_dir, f"timeline_{cat}.otio")
        otio.adapters.write_to_file(timeline, out_path)
        generated.append((cat, len(rows), out_path))

    return generated, missing

# ── main ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("csv")
parser.add_argument("--originals", default=BASH_ROOT)
args = parser.parse_args()

print("Indexando arquivos de mídia…")
file_index = build_file_index(args.originals)
print(f"  {len(file_index)} arquivos indexados")

results, missing = build_per_category(args.csv, file_index)

print(f"\n✓ {len(results)} timelines geradas:\n")
for cat, n, path in results:
    print(f"  [{n:3d} clips]  {os.path.basename(path)}")

if missing:
    print(f"\n⚠  {len(missing)} stems sem arquivo encontrado:")
    for s in sorted(missing):
        print(f"    {s}")
print()



