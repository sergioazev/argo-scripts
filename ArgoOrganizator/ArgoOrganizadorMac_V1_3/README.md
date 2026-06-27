---
type: note
domain: unclassified
date: 2026-05-24
status: work-in-progress
---
# Argo Organizador Mac V1

App macOS em Electron para:

- criar estruturas predefinidas
- copiar estrutura existente sem copiar arquivos
- criar estrutura manual
- preview antes de aplicar
- criar pastas reais
- renomear arquivos em lote
- rollback da última renomeação
- slug técnico compatível com Cinemateca/Netflix
- leitura opcional de metadata via ffprobe, se instalado

## Rodar

```bash
cd ArgoOrganizadorMac_V1
npm install
npm start
```

## Gerar app macOS

```bash
npm run dist
```

O app sai em:

```bash
dist/
```

## Instalar ffprobe opcional

```bash
brew install ffmpeg
```
