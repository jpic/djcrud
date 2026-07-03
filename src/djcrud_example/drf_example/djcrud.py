import djcrud
import djcrud_drf
from djcrud_example.views_example.models import Article
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product


class ProductViewSet(djcrud_drf.ModelViewSet):
    model = Product


djcrud_drf.site.register(ProductViewSet)


def can_publish(user, *, obj, **ctx):
    if not user.is_authenticated:
        return False
    if obj is not None and (
        not djcrud.is_owner(user, obj=obj, **ctx) or obj.published
    ):
        return False
    return True


class ArticleViewSet(djcrud_drf.ModelViewSet):
    model = Article

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.publish()
        return Response(self.get_serializer(article).data)


djcrud.add_perm(Article, "view,add,change,delete", check=djcrud.authenticated)
djcrud.add_perm(Article, "publish", check=can_publish)
djcrud_drf.site.register(ArticleViewSet)