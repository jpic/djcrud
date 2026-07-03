import djcrud

from .models import Page


class PageRouter(djcrud.ModelRouter):
    model = Page
    icon = "file-text"


djcrud.search.add_search(Page)
djcrud.site.routes.append(PageRouter)
