import djcrud

from .views import SiteSearchView

djcrud.site.routes.append(SiteSearchView)
