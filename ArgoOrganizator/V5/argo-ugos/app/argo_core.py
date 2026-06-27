import csv
import hashlib
import json
import os
import re
import shutil
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from templates_builtin import BASE_STRUCTURE, BUILTIN_TEMPLATES

MEDIA_EXTS = {".mov",".mp4",".mxf",".mkv",".avi",".wav",".aif",".aiff",".dpx",".exr",".tif",".tiff",".srt",".xml",".edl",".otio"}

AVID_PROFILES = {
    "FAST_AMA": {"link_mode": "symlink"},
    "PORTABLE_PACKAGE": {"link_mode": "copy"}
}

def data_root():
    return Path(os.environ.get("ARGO_DATA_ROOT", "/data"))

def templates_root():
    return data_root() / "templates"

def now_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def today():
    return datetime.now().strftime("%Y%m%d")

def slugify(text):
    text = str(text or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"^(a|o|as|os)\s+", "", text)
    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")

def ensure_data_dirs():
    templates_root().mkdir(parents=True, exist_ok=True)
    sample = templates_root() / "sample_template.json"
    if not sample.exists():
        sample.write_text(json.dumps({"name":"sample_template","paths":["_INGEST/ORIGINALS","_WORK/PROXIES","_EXPORT/MASTERS","_ARCHIVE/METADATA"]}, indent=2), encoding="utf-8")

def load_external_templates():
    ensure_data_dirs()
    out = {}
    for f in templates_root().glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            out[d.get("name") or f.stem] = d.get("paths", [])
        except Exception:
            pass
    return out

def all_templates():
    d = dict(BUILTIN_TEMPLATES)
    d.update(load_external_templates())
    return d

def render_path(p, slug, date):
    return p.replace("{slug}", slug).replace("{date}", date)

def get_template_paths(name, slug, date):
    t = all_templates().get(name)
    if t is None:
        raise ValueError(f"Template não encontrado: {name}")
    return sorted(set(BASE_STRUCTURE + [render_path(p, slug, date) for p in t]))

def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def create_structure(project_root, paths):
    created = existing = 0
    root = Path(project_root)
    for rel in paths:
        p = root / rel
        if p.exists():
            existing += 1
        else:
            p.mkdir(parents=True, exist_ok=True)
            created += 1
    return {"created_dirs": created, "existing_dirs": existing}

def compare_structure(project_root, expected):
    root = Path(project_root)
    actual = set()
    if root.exists():
        for r, dirs, _ in os.walk(root):
            for d in dirs:
                actual.add(str((Path(r)/d).relative_to(root)).replace("\\","/"))
    exp = set(expected)
    return {"missing": sorted(exp-actual), "extra": sorted(actual-exp)}

def clone_card(source, project_root, reel):
    src = Path(source)
    if not src.exists() or not src.is_dir():
        raise ValueError("source_path inválido")
    dst = Path(project_root) / "_INGEST" / "CARD_CLONES" / reel
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name.startswith("."):
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        elif not target.exists():
            shutil.copy2(item, target)
    return dst

def scan_media(folder):
    root = Path(folder)
    return sorted([p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in MEDIA_EXTS], key=lambda p: str(p).lower())

def partial_hash(path, size=1024*1024):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(size))
    return h.hexdigest()

def asset_id(slug, reel, date, i):
    return f"{slug}_{reel}_{date}_{str(i).zfill(3)}"

def build_records(config, source):
    slug = slugify(config["project_title"])
    reel = config.get("reel","A001")
    date = config.get("date") or today()
    target_dir = Path(config["project_root"]) / "_INGEST" / "ORIGINALS" / reel
    target_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for i, src in enumerate(scan_media(source), 1):
        aid = asset_id(slug, reel, date, i)
        ext = src.suffix.lower()
        avid = f"{slug[:4].upper()}_{reel}_{str(i).zfill(3)}"
        records.append({
            "index": i, "asset_id": aid, "avid_name": avid, "reel": reel,
            "original_name": src.name, "original_path": str(src),
            "new_name": f"{aid}{ext}", "new_path": str(target_dir / f"{aid}{ext}"),
            "ext": ext, "size": src.stat().st_size, "hash_partial": partial_hash(src)
        })
    return records

def copy_records(records, mode="copy"):
    out = []
    for r in records:
        src, dst = Path(r["original_path"]), Path(r["new_path"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        status = "exists"
        if not dst.exists():
            if mode == "move":
                shutil.move(str(src), str(dst))
            elif mode == "link":
                os.symlink(src, dst)
            else:
                shutil.copy2(src, dst)
            status = "created"
        item = dict(r); item["status"] = status; out.append(item)
    return out

def create_session(project_root, reel):
    sid = f"{now_id()}_ingest_{reel}"
    root = Path(project_root) / "_ARCHIVE" / "SESSIONS" / sid
    root.mkdir(parents=True, exist_ok=True)
    save_json(root / "session.json", {"id": sid, "reel": reel, "created_at": datetime.now().isoformat(), "operations": []})
    return root

def save_manifest(session_root, records, config):
    manifest = {"project": config.get("project_title"), "reel": config.get("reel"), "created_at": datetime.now().isoformat(), "records": records}
    save_json(Path(session_root)/"manifest.json", manifest)
    save_json(Path(config["project_root"]) / "_ARCHIVE" / "METADATA" / "manifests" / f"manifest_{Path(session_root).name}.json", manifest)
    return manifest

def update_inventory(project_root, records):
    root = Path(project_root) / "_ARCHIVE" / "METADATA"
    root.mkdir(parents=True, exist_ok=True)
    csv_path, json_path = root/"master_inventory.csv", root/"master_inventory.json"
    existing = []
    keys = set()
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing.append(row); keys.add(row.get("asset_id"))
    fields = ["asset_id","avid_name","reel","original_name","new_name","original_path","new_path","size","hash_partial","timestamp"]
    added = []
    for r in records:
        if r["asset_id"] in keys: continue
        added.append({k: r.get(k,"") for k in fields[:-1]} | {"timestamp": datetime.now().isoformat()})
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(existing + added)
    save_json(json_path, existing + added)
    return {"csv": str(csv_path), "json": str(json_path), "added": len(added)}

def generate_ale(records, ale_path):
    ale_path = Path(ale_path); ale_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ale_path, "w", encoding="utf-8") as f:
        f.write("Heading\nFIELD_DELIM\tTABS\nVIDEO_FORMAT\t1080\n\n")
        f.write("Column\nName\tTape\tSource File\tComments\n\nData\n")
        for r in records:
            f.write(f"{r['avid_name']}\t{r['reel']}\t{r['new_name']}\t{r['asset_id']}\n")
    return str(ale_path)

def avid_package(config, records):
    profile = AVID_PROFILES.get(config.get("avid_profile","FAST_AMA"), AVID_PROFILES["FAST_AMA"])
    avid = Path(config["project_root"]) / "_AVID"
    for d in ["ALE","LINK","REPORTS"]: (avid/d).mkdir(parents=True, exist_ok=True)
    by_reel = {}
    for r in records: by_reel.setdefault(r["reel"], []).append(r)
    ales = [generate_ale(rs, avid/"ALE"/f"{reel}.ale") for reel, rs in by_reel.items()]
    links = []
    for r in records:
        target = avid/"LINK"/r["reel"]/f"{r['avid_name']}{r['ext']}"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            if profile["link_mode"] == "copy": shutil.copy2(r["new_path"], target)
            else: os.symlink(Path(r["new_path"]), target)
            links.append(str(target))
    relink = avid/"REPORTS"/"relink_map.csv"
    with open(relink, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["asset_id","avid_name","reel","original_path","new_path","link_path","ale_name"])
        for r in records: w.writerow([r["asset_id"],r["avid_name"],r["reel"],r["original_path"],r["new_path"],f"_AVID/LINK/{r['reel']}/{r['avid_name']}{r['ext']}",f"{r['reel']}.ale"])
    assistant = avid/"REPORTS"/"assistant.csv"
    with open(assistant, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["avid_name","asset_id","reel","original_name","new_name"])
        for r in records: w.writerow([r["avid_name"],r["asset_id"],r["reel"],r["original_name"],r["new_name"]])
    save_json(avid/"REPORTS"/"bin_recipe.json", {"bins":[{"name":reel,"ale":f"ALE/{reel}.ale","link":f"LINK/{reel}/"} for reel in by_reel]})
    (avid/"README_IMPORT_AVID.txt").write_text(f"ARGO AVID PACKAGE\nProjeto: {config.get('project_title')}\n\n1. Importar ALE em _AVID/ALE.\n2. Link Media apontando para _AVID/LINK.\n3. Relink por Tape/Reel se necessário.\n", encoding="utf-8")
    pkg = Path(config["project_root"]) / "avid_package"
    if pkg.exists(): shutil.rmtree(pkg)
    shutil.copytree(avid, pkg, symlinks=True)
    return {"avid_root": str(avid), "ale_files": ales, "links_created": len(links), "avid_package": str(pkg)}

def project_json(config):
    path = Path(config["project_root"]) / "argo_project.json"
    data = {"project_title": config.get("project_title"), "slug": slugify(config.get("project_title")), "template": config.get("template"), "created_at": datetime.now().isoformat(), "nle_targets":["avid","resolve"]}
    save_json(path, data)
    return str(path)

def preview_ingest(config):
    slug = slugify(config.get("project_title"))
    date = config.get("date") or today()
    reel = config.get("reel","A001")
    root = Path(config["project_root"])
    paths = get_template_paths(config.get("template","Base_Editorial"), slug, date)
    files = scan_media(config["source_path"]) if config.get("source_path") else []
    records = []
    target = root / "_INGEST" / "ORIGINALS" / reel
    for i, f in enumerate(files, 1):
        aid = asset_id(slug, reel, date, i)
        records.append({"index": i, "original_name": f.name, "asset_id": aid, "target": str(target / f"{aid}{f.suffix.lower()}")})
    token_seed = json.dumps({"config": config, "time": time.time()}, sort_keys=True).encode("utf-8")
    token = hashlib.sha256(token_seed).hexdigest()
    dry = data_root() / "dry_runs"; dry.mkdir(parents=True, exist_ok=True)
    save_json(dry/f"{token}.json", {"config": config, "created_at": time.time()})
    return {"dry_run_token": token, "slug": slug, "reel": reel, "files_found": len(files), "records_preview": records, "structure_diff": compare_structure(root, paths)}

def validate_token(config, token):
    if not token: raise ValueError("dry_run_token ausente")
    path = data_root()/ "dry_runs" / f"{token}.json"
    if not path.exists(): raise ValueError("dry_run_token inválido")
    old = json.loads(path.read_text(encoding="utf-8")).get("config", {})
    for k in ["project_title","source_path","project_root","reel"]:
        if str(old.get(k)) != str(config.get(k)): raise ValueError(f"dry_run_token não corresponde: {k}")

def apply_ingest(config):
    validate_token(config, config.get("dry_run_token"))
    root = Path(config["project_root"]); root.mkdir(parents=True, exist_ok=True)
    slug = slugify(config["project_title"]); date = config.get("date") or today(); reel = config.get("reel","A001")
    paths = get_template_paths(config.get("template","Base_Editorial"), slug, date)
    structure = create_structure(root, paths)
    project_file = project_json(config)
    session = create_session(root, reel)
    working = clone_card(config["source_path"], root, reel) if config.get("clone_card", True) else Path(config["source_path"])
    records = build_records(config, working)
    if config.get("rename", True): records = copy_records(records, config.get("material_mode","copy"))
    manifest = save_manifest(session, records, config)
    inv = update_inventory(root, records)
    avid = avid_package(config, records) if config.get("avid_package", False) else None
    save_json(session/"session.json", {"id": session.name, "reel": reel, "project_file": project_file, "operations": [{"structure": structure}, {"records": len(records)}, {"inventory": inv}, {"avid": avid}]})
    return {"project_root": str(root), "session_root": str(session), "structure": structure, "records": len(records), "inventory": inv, "avid": avid}
