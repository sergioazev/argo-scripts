# argo-scripts

Coletânea de scripts e ferramentas de apoio à pós-produção da
[Argonautas](https://argonautas.tv) (LAB de pós-produção, Brasília-DF).

## Conteúdo

### `argo-scripts-legados/`
Scripts diversos: checklist de build (`build_checklist.py`), geração de docx
(`build_docx.js`), substituição de áudio (`replace_audio.py`).

### `passadopresente-scripts/`
Ferramentas de timeline/marcadores para o projeto *Passado Presente*:
interoperação OTIO (`argo_otio.py`, `resolve_import_otio.py`) e marcadores no
DaVinci Resolve (`resolve_add_markers.py`, `console_add_markers.py`).

### `folder-sync/`
`folder_sync.py` — sincronização de pasta origem → destino via `rsync`, com
`--dry-run`, `--delete` e log em arquivo. Portado do FolderSync.app
(AppleScript) do [POST-TOOLS](https://github.com/Hootan-H/POST-TOOLS).

### ArgoOrganizator → repositório próprio
O organizador/ingest de mídia (Python + Electron + Flask/Docker) virou um
projeto separado: **https://github.com/sergioazev/ArgoOrganizator**

## Licença

[MIT](LICENSE) — © 2026 Sérgio Azevedo / Argonautas.
