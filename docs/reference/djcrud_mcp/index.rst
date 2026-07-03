djcrud_mcp
~~~~~~~~~~

Optional stdio MCP bridge for djcrud. Discovers tools from the DRF OpenAPI
schema at ``/api/schema/`` and proxies authenticated HTTP calls to
``/api/`` — the agent surface parallel to :doc:`../djcrud_drf/index`.

Install the **client** extra on the machine that runs the MCP subprocess:

.. code-block:: bash

   pip install --pre "djcrud[mcp]"

This pulls ``mcp`` (FastMCP) and ``httpx``. Core djcrud has **no** MCP
dependency.

The **Django host** must already have :doc:`../djcrud_drf/index` and
:doc:`../djcrud_api/index` enabled. See :doc:`../../tutorial/frontend` and
:doc:`../../tutorial/agents`.

Design spec
===========

See :doc:`../../design/djcrud_mcp` for architecture, auth flow, tag-based
discovery, and package boundaries.

Server setup
============

1. Install API stack:

.. code-block:: bash

   pip install --pre "djcrud[drf]"

2. Add apps, middleware, and URLs (from :doc:`../../tutorial/frontend`).

3. Tag DRF endpoints for MCP discovery:

.. code-block:: python

   from drf_spectacular.utils import extend_schema
   import djcrud_drf

   class ItemViewSet(djcrud_drf.ModelViewSet):
       model = Item

       @extend_schema(tags=["myapp-items"], operation_id="item_list")
       def list(self, request, *args, **kwargs):
           return super().list(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_create")
       def create(self, request, *args, **kwargs):
           return super().create(request, *args, **kwargs)

   djcrud_drf.site.register(ItemViewSet)

4. Register permissions in ``djcrud.py`` — same rules as HTML (see
   :doc:`../../tutorial/permission`).

5. Verify schema:

.. code-block:: bash

   curl -s http://127.0.0.1:8000/api/schema/ | jq '.paths | keys'

Client setup
============

Environment variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 28 22 50

   * - Variable
     - Default
     - Purpose
   * - ``DJCRUD_BASE_URL``
     - ``http://127.0.0.1:8000``
     - API origin for schema fetch and tool calls
   * - ``DJCRUD_TOKEN``
     - *(empty)*
     - Bearer token (required for production subprocesses)
   * - ``DJCRUD_MCP_REGISTRY``
     - ``default``
     - Profile key (see :class:`~djcrud_mcp.RegistryProfile`)

Compatibility aliases (read in order, first match wins):

* Base URL: ``DJMVC_BASE_URL``, ``TILDETTE_BASE_URL``
* Token: ``DJMVC_TOKEN``, ``TILDETTE_TOKEN``

Console entry
-------------

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   export DJCRUD_BASE_URL=http://127.0.0.1:8000
   djcrud-mcp

One-shot tool invocation (no stdio MCP session):

.. code-block:: bash

   djcrud-mcp --call item_list --json '{}'

Without ``DJCRUD_TOKEN``, the CLI may exchange credentials via
``POST /api/login/`` using ``--user`` / ``--password`` (development only).

Authentication
==============

**Bearer token on every API call** — the MCP bridge sends:

.. code-block:: http

   Authorization: Bearer <DJCRUD_TOKEN>

Server middleware (:mod:`djcrud_api.middleware`) sets ``request.user`` from the
token row. Permissions run through :mod:`djcrud.permissions` on each ViewSet
action — identical to browser JSON or ``curl``.

Token sources:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Source
     - When to use
   * - ``Token.generate(user=..., name=...)``
     - Host spawns agent subprocess; inject raw key into env (recommended)
   * - ``POST /api/login/``
     - Local dev, CI, manual CLI
   * - HTML ``/api/token/`` create form
     - Long-lived personal API tokens

Passwords are **never** sent on individual tool calls.

Registry profiles
=================

A :class:`~djcrud_mcp.RegistryProfile` defines one stdio MCP server:

.. code-block:: python

   from dataclasses import dataclass, field

   @dataclass(frozen=True)
   class RegistryProfile:
       key: str
       server_name: str
       openapi_tags: tuple[str, ...]
       instructions: str
       info_tool_name: str
       description_prefix: str = ""
       meta: dict = field(default_factory=dict)

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Role
   * - ``server_name``
     - FastMCP server name visible to the agent host
   * - ``openapi_tags``
     - Filter ``/api/schema/`` operations (replaces URL prefix filtering)
   * - ``instructions``
     - System prompt text for the MCP session
   * - ``info_tool_name``
     - Meta-tool returning ``meta`` JSON (capabilities, hints)
   * - ``description_prefix``
     - Prepended to each tool description (e.g. ``[Tasks] ``)

Register profiles before starting the server:

.. code-block:: python

   import djcrud_mcp

   djcrud_mcp.register_profile(my_profile)

Public API (planned)
====================

The package is documented before implementation. Planned exports:

* ``create_mcp_server(...)`` — build a FastMCP instance
* ``RegistryProfile`` — MCP server configuration (dataclass)
* ``register_profile(profile)`` — add a profile to the global registry
* ``ExtraTool`` — hand-written tool alongside schema-derived ones
* ``CrudApi`` — Bearer HTTP client (``request``, ``fetch_schema``, ``login``)
* ``filter_operations(schema, tags)`` — select OpenAPI operations for a profile
* ``build_tools(schema, profile)`` — MCP tool definitions from schema

Permissions
===========

MCP does not bypass the registry. If ``add_perm(Item, "view", ...)`` denies a
user, ``item_list`` returns 403 through HTTP — the tool handler surfaces the
JSON error to the agent.

Register queryset scopers before agent access:

.. code-block:: python

   djcrud.add_queryset(Item, scoper=my_scoper, router=ItemRouter)

OpenAPI
=======

Tool input schemas are built from each operation's parameters and
``requestBody`` (OpenAPI 3). List endpoints may expose filter query parameters
when documented in the schema.

Custom APIViews must use ``@extend_schema`` so they appear in
``GET /api/schema/`` and in the tagged tool set.

What this package is not
========================

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Not
     - Use instead
   * - User MCP config vault / secrets store
     - Application code (e.g. Tildette ``djacp_mcp``)
   * - CRUD JSON routes
     - :doc:`../djcrud_drf/index`
   * - Bearer token storage
     - :doc:`../djcrud_api/index`
   * - HTML admin UI
     - :doc:`../site`

Further reading
===============

* :doc:`../../tutorial/agents` — end-to-end walkthrough
* :doc:`../../design/djcrud_mcp` — design spec
* :doc:`../../philosophy` — one permissions framework, every surface