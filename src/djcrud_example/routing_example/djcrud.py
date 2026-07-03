import djcrud

from .models import Item

djcrud.site.routes.append(
    djcrud.ModelRouter.clone(
        model=Item,
        icon="inbox",
    )
)
