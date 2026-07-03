# djcrud-client

Stdio MCP bridge for [djcrud](https://github.com/yourlabs/djcrud) JSON APIs. No Django required in the subprocess — FastMCP runs here, not on the Django host.

## Install

```bash
pip install djcrud-client
djcrud-client -mcp
```

## Host setup

Declare `McpProfile` classes in your app's `djcrud.py` and register them on `djcrud_mcp.site` (see `djcrud_example/mcp_example/djcrud.py` in the djcrud repo).

Add `djcrud_mcp` to `INSTALLED_APPS` and include `djcrud_drf.site` URLs on the host. Register one `McpProfile` in your app's `djcrud.py` (see `mcp_example/djcrud.py`). Run `djcrud-client -mcp` with `DJCRUD_TOKEN` set.