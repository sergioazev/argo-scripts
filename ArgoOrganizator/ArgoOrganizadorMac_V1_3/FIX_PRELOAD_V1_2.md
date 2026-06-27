---
type: note
domain: unclassified
date: 2026-05-24
status: work-in-progress
---
# Correção V1.2

Corrige `window.ARGO` indefinido.

Mudanças:
- `sandbox: false` explicitado no BrowserWindow
- `os.homedir()` movido para o processo main
- preload reduzido a `electron`
- renderer agora mostra erro claro se preload falhar

Procedimento recomendado:

```bash
rm -rf node_modules package-lock.json dist
npm install
npm start
```
