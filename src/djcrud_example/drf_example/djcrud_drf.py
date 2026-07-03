import djcrud_drf

from .models import Product


class ProductViewSet(djcrud_drf.ModelViewSet):
    model = Product


djcrud_drf.site.register(ProductViewSet)