import djcrud_mcp
from djcrud_example.drf_example.djcrud import ArticleViewSet, ProductViewSet


class ArticlesMcp(djcrud_mcp.McpProfile):
    key = "articles"
    default = True
    viewsets = (ArticleViewSet,)


class ProductsMcp(djcrud_mcp.McpProfile):
    key = "products"
    viewsets = (ProductViewSet,)


djcrud_mcp.site.register(ArticlesMcp)
djcrud_mcp.site.register(ProductsMcp)