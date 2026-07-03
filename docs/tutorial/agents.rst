Agents (MCP bridge)
===================

Stdio MCP tools proxy Bearer HTTP to your DRF API. Enable DRF first
(:doc:`drf`).

The MCP **client** is the standalone ``djcrud-mcp`` package (``mcp`` +
``httpx`` only — no Django). The Django **host** still needs
:doc:`../reference/djcrud_drf/index` and :doc:`../reference/djcrud_api/index`.

Install client
--------------

**Remote subprocesses** (no Django on ``PYTHONPATH`` — sandboxes, CI, remote agents):

.. code-block:: bash

   pip install --pre djcrud-mcp

**Django host** (declare profiles and serve ``GET /api/mcp/profiles/``):

.. code-block:: bash

   pip install --pre "djcrud[drf,mcp]"

Remote agents install ``djcrud-mcp`` only and point at your API with
``DJCRUD_BASE_URL`` / ``DJCRUD_TOKEN``. The client fetches the active profile
from the host at startup.

Example
-------

Base ViewSet registration lives in ``drf_example/djcrud.py`` (see :doc:`drf`).
Custom ``@action`` methods — such as **publish** on ``Article`` — can live in a
separate module imported from ``djcrud.py``. MCP tools (``article_list``,
``article_create``, ``article_publish``, …) follow from the registered ViewSet
and ``GET /api/schema/``.

.. literalinclude:: ../../src/djcrud_example/drf_example/article_viewset.py

Default profile
---------------

With no ``McpProfile`` registered, the ``default`` profile exposes every
``ModelViewSet`` on :data:`djcrud_drf.site`:

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp -mcp

Named profiles
--------------

When you need **multiple** stdio MCP servers (tasks vs admin, public vs internal),
declare a :class:`~djcrud_mcp.McpProfile` on the Django host and register it on
:data:`djcrud_mcp.site` — same pattern as :meth:`djcrud_drf.site.register`:

.. code-block:: python

   import djcrud_mcp
   from myapp.drf import ArticleViewSet

   class ArticlesMcp(djcrud_mcp.McpProfile):
       key = "articles"
       server_name = "myapp-articles"
       instructions = "Article CRUD via /api/article/."
       info_tool_name = "article_registry_info"
       viewsets = (ArticleViewSet,)

   djcrud_mcp.site.register(ArticlesMcp)

Wire host URLs (once per project):

.. code-block:: python

   from djcrud_mcp.django.urls import urlpatterns as mcp_urlpatterns

   urlpatterns = [
       # ...
   ] + djcrud_drf.site.build().urlpatterns + mcp_urlpatterns

Remote client:

.. code-block:: bash

   export DJCRUD_MCP_REGISTRY=articles
   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp -mcp

The client calls ``GET /api/mcp/profiles/articles/`` for instructions and API
prefixes, then ``GET /api/schema/`` to build tools.

Run
---

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp --call article_list --json '{}'
   djcrud-mcp --call article_publish --json '{"pk": 1}'
   djcrud-mcp -mcp

Reference: :doc:`../reference/djcrud_mcp/index`.