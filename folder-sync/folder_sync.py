#!/usr/bin/env python3
"""
Folder Sync — Argonautas Lab
Sincroniza uma pasta origem para uma pasta destino via rsync.
Baseado no FolderSync.app (AppleScript) do POST-TOOLS
(https://github.com/Hootan-H/POST-TOOLS), portado para CLI com
log em arquivo e modo dry-run.

Requisitos:
  - Python 3.8+ (já vem no macOS)
  - rsync (já vem no macOS)
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def build_rsync_cmd(source: Path, destination: Path, dry_run: bool, delete: bool) -> list[str]:
    cmd = ["rsync", "-av"]
    if dry_run:
        cmd.append("--dry-run")
    if delete:
        cmd.append("--delete")
    cmd += [f"{source}/", str(destination)]
    return cmd


def run_sync(source: str, destination: str, dry_run: bool, delete: bool, log_path: Path | None) -> int:
    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()

    if not source_path.is_dir():
        print(f"Erro: pasta origem não encontrada: {source_path}", file=sys.stderr)
        return 1
    destination_path.mkdir(parents=True, exist_ok=True)

    cmd = build_rsync_cmd(source_path, destination_path, dry_run, delete)
    print(f"$ {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if log_path:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} ===\n")
            log_file.write(f"$ {' '.join(cmd)}\n")
            log_file.write(result.stdout)
            if result.stderr:
                log_file.write(result.stderr)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Sincroniza pasta origem → destino via rsync.")
    parser.add_argument("source", help="Pasta origem")
    parser.add_argument("destination", help="Pasta destino")
    parser.add_argument("--dry-run", action="store_true", help="Simula a sincronização sem copiar nada")
    parser.add_argument("--delete", action="store_true", help="Remove no destino arquivos que não existem mais na origem")
    parser.add_argument("--log", metavar="ARQUIVO", help="Caminho do arquivo de log (append)")
    args = parser.parse_args()

    log_path = Path(args.log).expanduser() if args.log else None
    returncode = run_sync(args.source, args.destination, args.dry_run, args.delete, log_path)
    sys.exit(returncode)


if __name__ == "__main__":
    main()
