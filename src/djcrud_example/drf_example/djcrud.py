import djcrud

from .models import Product


class ProductRouter(djcrud.ModelRouter):
    model = Product
    icon = "box"


djcrud.site.routes.append(ProductRouter)