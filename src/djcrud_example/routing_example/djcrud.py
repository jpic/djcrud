import djcrud

from .models import Item

djcrud.add_search(Item)
djcrud.site.routes.append(
    djcrud.ModelRouter.clone(
        model=Item,
        icon="inbox",
    )
)
