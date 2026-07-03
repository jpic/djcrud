import djcrud_drf

from djcrud_mcp.api_viewsets import McpProfileViewSet, McpViewsetCatalogViewSet

djcrud_drf.site.register(McpProfileViewSet)
djcrud_drf.site.register(McpViewsetCatalogViewSet)