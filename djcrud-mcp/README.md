# djcrud-mcp (compatibility shim)

The MCP stdio client moved to **`djcrud-client`**. The Django host package is
**`djcrud_mcp`** inside the main `djcrud` wheel.

This directory exists so older install paths (`pip install -e ./djcrud-mcp`) keep
working in CI and docs until workflows are updated.

```bash
pip install djcrud-client
```
