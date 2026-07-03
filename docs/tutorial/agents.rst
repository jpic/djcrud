Agents (MCP bridge)
===================

Stdio MCP tools proxy Bearer HTTP to your DRF API. Enable DRF first
(:doc:`frontend`).

The MCP **client** is the standalone ``djcrud-mcp`` package (``mcp`` +
``httpx`` only — no Django). The Django **host** still needs
:doc:`../reference/djcrud_drf/index` and :doc:`../reference/djcrud_api/index`.

Install client
--------------

**Sandboxes and agent subprocesses** (no Django on ``PYTHONPATH``):

.. code-block:: bash

   pip install --pre djcrud-mcp

**Django host development** (ViewSet auto-discovery via ``djcrud_drf.site``):

.. code-block:: bash

   pip install --pre "djcrud[drf,mcp]"

``djcrud[mcp]`` depends on ``djcrud-mcp``; use ``[drf,mcp]`` when the MCP
process runs on the same machine as Django and should introspect registered
ViewSets. Remote agents should install ``djcrud-mcp`` only and point at your
API with ``DJCRUD_BASE_URL`` / ``DJCRUD_TOKEN``.

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

Standalone registry (no ViewSet introspection)
--------------------------------------------

When the MCP subprocess cannot import Django (gVisor sandboxes, CI, remote
agents), register a :class:`~djcrud_mcp.RegistryProfile` with ``api_prefixes``
and optional :class:`~djcrud_mcp.ExtraTool` entries — then run ``djcrud-mcp``:

.. code-block:: python

   from djcrud_mcp import ExtraTool, RegistryProfile, register_profile

   register_profile(
       RegistryProfile(
           key="articles",
           server_name="myapp-articles",
           instructions="Article CRUD via /api/article/.",
           info_tool_name="article_registry_info",
           api_prefixes=("/api/article/",),
           extra_tools=(
               ExtraTool(
                   name="article_publish",
                   method="post",
                   path="/api/article/{id}/publish/",
                   description="Publish an article",
                   input_schema={
                       "type": "object",
                       "properties": {"id": {"type": "integer"}},
                       "required": ["id"],
                   },
               ),
           ),
       )
   )

.. code-block:: bash

   export DJCRUD_MCP_REGISTRY=articles
   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp -mcp

On a Django host, the same profile works without ``discover_viewsets()`` as long
as ``api_prefixes`` is set.

Run
---

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp --call article_list --json '{}'
   djcrud-mcp --call article_publish --json '{"pk": 1}'
   djcrud-mcp -mcp

Reference: :doc:`../reference/djcrud_mcp/index`.