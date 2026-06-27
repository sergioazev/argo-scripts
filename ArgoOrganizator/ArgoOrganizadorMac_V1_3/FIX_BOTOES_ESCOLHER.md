---
type: note
domain: unclassified
date: 2026-05-24
status: work-in-progress
---
# Correção V1.1

Correção aplicada:

- removido uso de `process.env.HOME` no renderer
- `home()` exposto pelo preload via `os.homedir()`
- botões `Escolher...` agora usam `addEventListener`
- logs de erro visíveis no app
- package.json corrigido: `electron` em devDependencies

Rodar:

```bash
npm install
npm start
```

Build:

```bash
npm run dist
```
