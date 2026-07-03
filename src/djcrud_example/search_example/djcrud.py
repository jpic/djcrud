import djcrud

from .models import Page


class PageRouter(djcrud.ModelRouter):
    model = Page
    icon = "file-text"


djcrud.permissions.add_search(Page)
djcrud.site.routes.append(PageRouter)
