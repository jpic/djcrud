import djcrud

from .example_action import PublishView
from .example_listaction import post_router
from .example_listview import ArticleRouter
from .models import Article


def can_publish(user, *, obj, **ctx):
    if not user.is_authenticated:
        return False
    if obj is not None and (
        not djcrud.is_owner(user, obj=obj, **ctx) or obj.published
    ):
        return False
    return True


class ArticleCreateView(djcrud.generic.CreateView):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


article_routes = []
for route in ArticleRouter.routes:
    if route is djcrud.generic.CreateView:
        article_routes.append(ArticleCreateView)
    else:
        article_routes.append(route)
article_routes.append(PublishView)

article_router = ArticleRouter.clone(routes=article_routes)

djcrud.add_perm(article_router, "view,add,change,delete", check=djcrud.authenticated)
djcrud.add_perm(Article, "publish", check=can_publish)
djcrud.site.routes.append(article_router)
djcrud.site.routes.append(post_router)