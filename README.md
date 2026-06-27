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

### `ArgoOrganizator/`
Organizador/ingest de mídia em três encarnações:
- `ArgoOrganizador.py` — versão script Python
- `ArgoOrganizadorMac_V1_3/` — app Electron (macOS)
- `V5/argo-ugos/` — serviço Flask + Docker com preview/apply de ingest
  (dry-run por token, templates de estrutura de pastas)

## Licença

[MIT](LICENSE) — © 2026 Sérgio Azevedo / Argonautas.
