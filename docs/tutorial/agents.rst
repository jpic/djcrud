Agents (MCP bridge)
===================

Stdio MCP tools proxy Bearer HTTP to your DRF API. Enable DRF first
(:doc:`frontend`).

Install client
--------------

.. code-block:: bash

   pip install --pre "djcrud[mcp]"

Example
-------

One ``djcrud.py`` — CRUD permissions, ``publish`` action, ViewSet registration.
MCP tools (``article_list``, ``article_create``, ``article_publish``, …) follow
from the registered ViewSet and ``GET /api/schema/``.

.. code-block:: python

   import djcrud
   import djcrud_drf
   from rest_framework.decorators import action
   from rest_framework.response import Response

   from .models import Article


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

Run
---

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp --call article_list --json '{}'
   djcrud-mcp --call article_publish --json '{"pk": 1}'

Reference: :doc:`../reference/djcrud_mcp/index`.