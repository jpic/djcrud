import djcrud

from .views import AutocompleteView

djcrud.ModelRouter.routes.append(AutocompleteView)
