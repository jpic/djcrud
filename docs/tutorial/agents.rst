Agents (MCP bridge)
===================

Stdio MCP tools proxy Bearer HTTP to your DRF API. Enable DRF first
(:doc:`drf`).

Two packages:

* **``djcrud_mcp``** (Django host, inside ``djcrud``) — ``McpProfile`` registration,
  ``GET /api/mcp/profiles/``
* **``djcrud-client``** (agent subprocess) — FastMCP stdio server, OpenAPI tool
  generation, HTTP proxy (``mcp`` + ``httpx`` only — no Django)

Install
-------

**Remote subprocesses** (sandboxes, CI, remote agents):

.. code-block:: bash

   pip install --pre djcrud-client

**Django host** (declare profiles and serve ``GET /api/mcp/profiles/``):

.. code-block:: bash

   pip install --pre "djcrud[drf,mcp]"

Remote agents install ``djcrud-client`` only and point at your API with
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

MCP profiles (host)
-------------------

Declare a :class:`~djcrud_mcp.McpProfile` on the Django host and register it on
:data:`djcrud_mcp.site` — same pattern as :meth:`djcrud_drf.site.register`.
Every stdio MCP client uses a registered profile; remote clients fetch it from
``GET /api/mcp/profiles/{key}/`` at startup.

.. code-block:: python

   import djcrud_mcp
   from myapp.drf import ArticleViewSet

   class ArticlesMcp(djcrud_mcp.McpProfile):
       key = "articles"
       viewsets = (ArticleViewSet,)

   djcrud_mcp.site.register(ArticlesMcp)

MCP profile routes are mounted automatically under ``/api/mcp/`` when you include
:data:`djcrud_drf.site` URLs (same as schema and login):

.. code-block:: python

   urlpatterns = [
       # ...
   ] + djcrud_drf.site.build().urlpatterns

Remote client
-------------

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-client -mcp --registry articles

The client calls ``GET /api/mcp/profiles/{key}/`` for instructions and API
prefixes, then ``GET /api/schema/`` to build tools. Omit ``--registry`` to use
the host default from ``GET /api/mcp/profiles/``.

Run
---

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-client --call article_list --json '{}'
   djcrud-client --call article_publish --json '{"pk": 1}'
   djcrud-client -mcp

Reference: :doc:`../reference/djcrud_mcp/index`.