# djcrud-mcp

Stdio MCP client for djcrud JSON APIs. Depends only on `mcp` and `httpx` — no Django.

Use when the MCP subprocess runs outside the Django host (sandboxes, agents, CI).

```bash
pip install djcrud-mcp
export DJCRUD_TOKEN=<token>
djcrud-mcp -mcp
```

Register tools via `api_prefixes` on a `RegistryProfile` (no ViewSet introspection), or
install `djcrud-mcp[django]` on a Django host for automatic ViewSet discovery.