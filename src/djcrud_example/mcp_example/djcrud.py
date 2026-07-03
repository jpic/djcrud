import djcrud_mcp
from djcrud_example.drf_example.djcrud import ArticleViewSet, ProductViewSet


class ExampleMcp(djcrud_mcp.McpProfile):
    viewsets = (ArticleViewSet, ProductViewSet)


djcrud_mcp.site.register(ExampleMcp)