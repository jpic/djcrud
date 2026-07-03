import djcrud

from .models import Article


class ArticleRouter(djcrud.ModelRouter):
    model = Article
    icon = "newspaper"

    routes = djcrud.ModelRouter.routes + [
        djcrud.views.ListView.clone(
            table_fields=["title", "category"],
            filter_fields=["category"],
            paginate_by=5,
        ),
    ]


djcrud.site.routes.append(ArticleRouter)
