Agents (MCP bridge)
===================

Stdio MCP tools proxy Bearer HTTP to your DRF API. Enable DRF first
(:doc:`drf`).

Two packages:

* **``djcrud_mcp``** (Django host, inside ``djcrud``) — ``McpProfile`` registration
* **``djcrud-client``** (agent subprocess) — FastMCP stdio server, OpenAPI tool
  generation, HTTP proxy (``mcp`` + ``httpx`` only — no Django)

Install
-------

**Remote subprocesses** (sandboxes, CI, remote agents):

.. code-block:: bash

   pip install --pre djcrud-client

**Django host**:

.. code-block:: bash

   pip install --pre "djcrud[drf,mcp]"

Remote agents install ``djcrud-client`` only and point at your API with
``DJCRUD_BASE_URL`` / ``DJCRUD_TOKEN``.

Example apps
------------

* ``drf_example`` — ViewSets at ``/api/`` (see :doc:`drf`)
* ``mcp_example`` — the project's MCP profile (this chapter)

ViewSet registration lives in ``drf_example/djcrud.py``. The ``publish``
``@action`` on ``ArticleViewSet`` becomes an MCP tool (``article_publish``) via
``GET /api/schema/``:

.. literalinclude:: ../../src/djcrud_example/drf_example/djcrud.py
   :lines: 18-38

MCP profile
-----------

Register one :class:`~djcrud_mcp.McpProfile` in ``djcrud.py`` — that is the MCP
surface for your project. List the ViewSets agents may call (same models as
:doc:`drf`):

.. literalinclude:: ../../src/djcrud_example/mcp_example/djcrud.py

Add ``djcrud_mcp`` and your MCP app to ``INSTALLED_APPS``. The ``djcrud_mcp``
package registers the profile HTTP API on :data:`djcrud_drf.site`; your app's
``djcrud.py`` registers the profile itself:

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

Run
---

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-client --call article_list --json '{}'
   djcrud-client --call article_publish --json '{"pk": 1}'
   djcrud-client -mcp

Reference: :doc:`../reference/djcrud_mcp/index`.