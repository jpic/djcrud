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

Example apps
------------

* ``drf_example`` — ViewSets at ``/api/`` (see :doc:`drf`)
* ``mcp_example`` — ``McpProfile`` classes for stdio MCP clients (this chapter)

ViewSet registration lives in ``drf_example/djcrud.py``. The ``publish``
``@action`` on ``ArticleViewSet`` becomes an MCP tool (``article_publish``) via
``GET /api/schema/``:

.. literalinclude:: ../../src/djcrud_example/drf_example/djcrud.py
   :lines: 27-39

MCP profiles
------------

Declare :class:`~djcrud_mcp.McpProfile` classes in the app's ``djcrud.py`` and
register them on :data:`djcrud_mcp.site` — same pattern as
:meth:`djcrud_drf.site.register`. The tutorial app ``mcp_example`` wires
``ArticleViewSet`` and ``ProductViewSet`` from ``drf_example``:

.. literalinclude:: ../../src/djcrud_example/mcp_example/djcrud.py

Add ``djcrud_mcp`` and your MCP app to ``INSTALLED_APPS``. The ``djcrud_mcp``
package registers profile API ViewSets on :data:`djcrud_drf.site`; your app's
``djcrud.py`` registers the profiles agents actually use:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "djcrud_drf",
       "djcrud_mcp",
       "djcrud_example.mcp_example",
   ]

   urlpatterns = (
       djcrud.site.build().urlpatterns
       + djcrud_drf.site.build().urlpatterns
   )

Remote client
-------------

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-client -mcp --registry articles

The client calls ``GET /api/mcp/profiles/{key}/`` for instructions and API
prefixes, then ``GET /api/schema/`` to build tools. Omit ``--registry`` to use
the host default from ``GET /api/mcp/profiles/`` (``articles`` in the example).

Run
---

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-client --call article_list --json '{}'
   djcrud-client --call article_publish --json '{"pk": 1}'
   djcrud-client -mcp

Reference: :doc:`../reference/djcrud_mcp/index`.