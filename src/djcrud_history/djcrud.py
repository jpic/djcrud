import djcrud

from .views import LogEntryRouter

djcrud.site.routes.append(LogEntryRouter)
