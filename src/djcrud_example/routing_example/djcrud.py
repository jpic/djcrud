import djcrud

from .models import Item


class ItemRouter(djcrud.ModelRouter):
    model = Item
    icon = "inbox"
    routes = djcrud.ModelRouter.routes + [
        djcrud.generic.ListView.clone(site_search=True),
    ]


djcrud.site.routes.append(ItemRouter)