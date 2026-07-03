# djcrud-mcp (compatibility shim)

The MCP stdio client lives in **`djcrud-client`**; this package keeps the legacy
``pip install -e ./djcrud-mcp`` path working in older CI workflows.

```bash
pip install djcrud-client   # preferred
djcrud-client -mcp
```
