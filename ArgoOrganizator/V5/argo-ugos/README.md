---
type: note
domain: unclassified
date: 2026-05-24
status: work-in-progress
---
# Argo UGOS

ArgoOrganizador para UGREEN NAS / UGOS via Docker.

## Inclui

- Web UI em `http://IP_DO_NAS:8787`
- API Flask
- Docker + docker-compose
- Templates internos e externos
- Fluxo único de ingest
- Card Clone
- Estrutura base obrigatória
- Rename/copy com AssetID
- Dry-run obrigatório
- Ingest Session
- Manifest por sessão
- Master Inventory CSV/JSON
- Comparador de estrutura
- Avid Package:
  - ALE por reel
  - Link Farm por symlink ou copy
  - Relink Map
  - Assistant CSV
  - bin_recipe.json
  - README_IMPORT_AVID.txt

Sem QC.

## Instalação UGOS

Ajuste volumes em `docker-compose.yml`:

```yaml
- /volume1/Projetos:/projects
- /volume1/ArgoData:/data
```

Depois:

```bash
docker compose up -d --build
```

Acesse:

```text
http://IP_DO_UGREEN:8787
```

## Templates externos

Coloque arquivos `.json` em:

```text
/data/templates/
```

Formato:

```json
{
  "name": "Meu_Template",
  "paths": [
    "_INGEST/ORIGINALS",
    "_WORK/PROXIES",
    "_EXPORT/MASTERS",
    "_ARCHIVE/METADATA"
  ]
}
```
