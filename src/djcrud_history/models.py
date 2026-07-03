import djcrud

from .views import HistoryView

djcrud.ModelRouter.routes.append(HistoryView)
