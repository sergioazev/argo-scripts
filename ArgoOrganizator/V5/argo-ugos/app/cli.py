import argparse, json
import argo_core as argo

p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd")
a = sub.add_parser("preview"); a.add_argument("config")
b = sub.add_parser("apply"); b.add_argument("config")
sub.add_parser("templates")
args = p.parse_args()

if args.cmd == "templates":
    print(json.dumps(sorted(argo.all_templates().keys()), indent=2, ensure_ascii=False))
elif args.cmd in ("preview", "apply"):
    cfg = json.loads(open(args.config, encoding="utf-8").read())
    out = argo.preview_ingest(cfg) if args.cmd == "preview" else argo.apply_ingest(cfg)
    print(json.dumps(out, indent=2, ensure_ascii=False))
else:
    p.print_help()
