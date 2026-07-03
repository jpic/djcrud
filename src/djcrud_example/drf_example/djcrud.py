import djcrud

from .models import Product


class ProductRouter(djcrud.ModelRouter):
    model = Product
    icon = "box"


djcrud.site.routes.append(ProductRouter)

try:
    import djcrud_drf
except ImportError:
    djcrud_drf = None

if djcrud_drf is not None:

    class ProductViewSet(djcrud_drf.ModelViewSet):
        model = Product

    djcrud_drf.site.register(ProductViewSet)