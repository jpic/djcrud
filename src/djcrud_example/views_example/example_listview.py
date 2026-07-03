import djcrud

from .models import Article


class CategoryUpdateView(djcrud.generic.UpdateView):
    """Update a single field — shows in the object action menu."""

    fields = ["category"]
    title = "Change category"
    icon = "tag"
    color = "info"


class ArticleRouter(djcrud.ModelRouter):
    model = Article
    icon = "newspaper"

    routes = djcrud.ModelRouter.routes + [
        djcrud.generic.ListView.clone(
            table_fields=["title", "category"],
            filter_fields=["category"],
            paginate_by=5,
        ),
        CategoryUpdateView,
    ]