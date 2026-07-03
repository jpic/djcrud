try:
    import djcrud_drf
except ImportError:
    djcrud_drf = None

if djcrud_drf is not None:
    # docs: product-viewset-begin
    from .models import Product

    class ProductViewSet(djcrud_drf.ModelViewSet):
        model = Product

    djcrud_drf.site.register(ProductViewSet)
    # docs: product-viewset-end

    from . import article_viewset  # noqa: F401