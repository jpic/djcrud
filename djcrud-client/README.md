# djcrud-client

Stdio MCP bridge for [djcrud](https://github.com/yourlabs/djcrud) JSON APIs. No Django required in the subprocess — FastMCP runs here, not on the Django host.

## Install

```bash
pip install djcrud-client
djcrud-client -mcp
```

## Host setup

Declare `McpProfile` classes on the Django host and register them on `djcrud_mcp.site` (like `djcrud_drf.site.register`):

```python
import djcrud_mcp

class ArticlesMcp(djcrud_mcp.McpProfile):
    key = "articles"
    viewsets = (ArticleViewSet,)

djcrud_mcp.site.register(ArticlesMcp)
```

Mount `djcrud_mcp.urls` so remote clients can fetch profiles at `GET /api/mcp/profiles/{key}/`. `GET /api/mcp/profiles/` also returns the host `default` key. Mark one profile with `default = True` (or register only one); clients omit `--registry` to use that default.