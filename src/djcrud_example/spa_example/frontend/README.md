# SPA example frontend

```bash
npm ci
npm run build
```

Build output (with content hashes + `.vite/manifest.json`) is written to
`../static/spa_example/js/` and committed for the tutorial. The Python side
resolves the stable name via ``djcrud.static.vite_asset``.