# djcrud-mcp

Stdio MCP client for djcrud JSON APIs. Depends only on `mcp` and `httpx` — no Django.

Use when the MCP subprocess runs outside the Django host (sandboxes, agents, CI).

```bash
pip install djcrud-mcp
export DJCRUD_TOKEN=<token>
djcrud-mcp -mcp
```

## Django host

Every stdio MCP client needs a host-registered profile. Declare `McpProfile` classes and register them on `djcrud_mcp.site` (like `djcrud_drf.site.register`):

```python
import djcrud_mcp

class ArticlesMcp(djcrud_mcp.McpProfile):
    key = "articles"
    viewsets = (ArticleViewSet,)

djcrud_mcp.site.register(ArticlesMcp)
```

Mount `djcrud_mcp.django.urls` so remote clients can fetch profiles at `GET /api/mcp/profiles/{key}/`.

`server_name`, `instructions`, and `info_tool_name` default from the profile key and ViewSets. Mark one profile with `default = True` (or register only one) so clients can resolve the registry without `DJCRUD_MCP_REGISTRY`.

CRUD tools come from `GET /api/schema/` filtered by the profile's ViewSets. Non-CRUD endpoints must be DRF routes documented with `@extend_schema`.