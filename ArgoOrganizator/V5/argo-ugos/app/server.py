from flask import Flask, jsonify, request, render_template_string
import os
import argo_core as argo

app = Flask(__name__)

PAGE = """
<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Argo UGOS</title>
<style>
body{background:#0b0b0d;color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;padding:28px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:#151519;border:1px solid #2a2a32;border-radius:16px;padding:16px}
label{display:block;color:#b8b8c2;font-size:12px;margin:10px 0 5px}input,select{width:100%;background:#0f0f13;color:#fff;border:1px solid #33333d;border-radius:10px;padding:9px;box-sizing:border-box}
button{background:#f5f5f5;color:#111;border:0;border-radius:10px;padding:10px 14px;margin-top:12px;cursor:pointer}.secondary{background:#2b2b35;color:#fff}pre{white-space:pre-wrap;background:#101014;border:1px solid #2a2a32;padding:14px;border-radius:12px;min-height:360px}
</style></head><body>
<h1>Argo UGOS</h1><p>Servidor de ingest e organização para UGREEN NAS. Sem QC.</p>
<div class="grid"><div class="card">
<h2>Ingest Pipeline</h2>
<label>Título</label><input id="project_title" value="O Cabra Marcado Para Morrer">
<label>Source Path no NAS</label><input id="source_path" value="/projects/_INBOX/A001">
<label>Project Root</label><input id="project_root" value="/projects/cabra">
<label>Reel</label><input id="reel" value="A001">
<label>Template</label><select id="template"></select>
<label>Avid Profile</label><select id="avid_profile"><option>FAST_AMA</option><option>PORTABLE_PACKAGE</option></select>
<label><input type="checkbox" id="clone_card" checked> Card Clone</label>
<label><input type="checkbox" id="rename" checked> Rename/Copy com AssetID</label>
<label><input type="checkbox" id="avid_package" checked> Gerar Avid Package</label>
<button onclick="preview()">Preview</button> <button class="secondary" onclick="apply()">Apply</button>
</div><div class="card"><h2>Resultado</h2><pre id="log">Pronto.</pre></div></div>
<script>
let dryRunToken="";
function log(x){document.getElementById("log").textContent=typeof x==="string"?x:JSON.stringify(x,null,2)}
function cfg(){return{project_title:project_title.value,source_path:source_path.value,project_root:project_root.value,reel:reel.value,template:template.value,avid_profile:avid_profile.value,clone_card:clone_card.checked,rename:rename.checked,avid_package:avid_package.checked,material_mode:"copy"}}
async function loadTemplates(){let r=await fetch("/api/templates");let d=await r.json();template.innerHTML=d.templates.map(t=>`<option value="${t}">${t}</option>`).join("");template.value="Base_Editorial"}
async function preview(){let r=await fetch("/api/ingest/preview",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(cfg())});let d=await r.json();if(d.dry_run_token)dryRunToken=d.dry_run_token;log(d)}
async function apply(){let c=cfg();c.dry_run_token=dryRunToken;let r=await fetch("/api/ingest/apply",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(c)});log(await r.json())}
loadTemplates()
</script></body></html>
"""

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/api/health")
def health():
    return jsonify({"ok": True, "projects_root": os.environ.get("ARGO_PROJECTS_ROOT","/projects"), "data_root": os.environ.get("ARGO_DATA_ROOT","/data")})

@app.route("/api/templates")
def templates():
    return jsonify({"templates": sorted(argo.all_templates().keys())})

@app.route("/api/ingest/preview", methods=["POST"])
def preview():
    try: return jsonify(argo.preview_ingest(request.get_json(force=True)))
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route("/api/ingest/apply", methods=["POST"])
def apply():
    try: return jsonify(argo.apply_ingest(request.get_json(force=True)))
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route("/api/structure/compare", methods=["POST"])
def compare():
    try:
        d=request.get_json(force=True); slug=argo.slugify(d.get("project_title")); date=d.get("date") or argo.today()
        paths=argo.get_template_paths(d.get("template"), slug, date)
        return jsonify(argo.compare_structure(d.get("project_root"), paths))
    except Exception as e: return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    argo.ensure_data_dirs()
    app.run(host="0.0.0.0", port=8787)
