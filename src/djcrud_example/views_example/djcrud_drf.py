from rest_framework.decorators import action
from rest_framework.response import Response

import djcrud_drf

from .models import Article


class ArticleViewSet(djcrud_drf.ModelViewSet):
    model = Article

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.publish()
        return Response(self.get_serializer(article).data)


djcrud_drf.site.register(ArticleViewSet)