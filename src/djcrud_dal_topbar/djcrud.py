import djcrud

from .views import SearchView, SiteSearchView

djcrud.site.routes.append(SearchView)
djcrud.site.routes.append(SiteSearchView)
