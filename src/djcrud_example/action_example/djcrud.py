import djcrud

from .models import Memo


class DuplicateView(djcrud.views.ObjectFormView):
    title = "Duplicate"
    icon = "copy"
    color = "info"

    def form_valid(self, form):
        Memo.objects.create(title=f"{self.object.title} (copy)")
        return super().form_valid(form)


class MemoRouter(djcrud.ModelRouter):
    model = Memo
    icon = "stickies"

    routes = djcrud.ModelRouter.routes + [DuplicateView]


djcrud.site.routes.append(MemoRouter)
