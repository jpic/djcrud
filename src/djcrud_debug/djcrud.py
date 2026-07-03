import djcrud

from .views import RoutingDebugRouter

djcrud.site.routes.append(RoutingDebugRouter)
