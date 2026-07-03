djcrud_mcp
~~~~~~~~~~

Optional stdio MCP bridge for djcrud. Exposes **registered**
:class:`~djcrud_drf.ModelViewSet` CRUD as MCP tools and proxies Bearer HTTP to
``/api/`` — permissions enforced on the server, same registry as HTML and DRF.

.. code-block:: bash

   pip install --pre "djcrud[mcp]"

Client extra: ``mcp``, ``httpx``. Django host needs :doc:`../djcrud_drf/index`
and :doc:`../djcrud_api/index`. See :doc:`../../tutorial/agents`.

Design spec: :doc:`../../design/djcrud_mcp`.

CRUD without decorators
=======================

Register a ViewSet the same way as :doc:`../../tutorial/drf`, then include it on
a registered :class:`~djcrud_mcp.McpProfile` — MCP tools follow from
``GET /api/schema/``:

.. code-block:: python

   # djcrud.py
   import djcrud_drf

   djcrud.site.routes.append(ItemRouter)
   djcrud.add_perm(ItemRouter, "view,add,change,delete", check=authenticated)
   djcrud_drf.site.register(ItemViewSet)

Open access in ``djcrud.py`` with :func:`~djcrud.add_perm` /
:func:`~djcrud.add_queryset` (see :doc:`../../tutorial/permission`). The agent
token is a normal Django user; ``item_list`` returns only rows that user may
view.

Generated MCP tools (no manual naming):

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Tool
     - HTTP
   * - ``item_list``
     - ``GET /api/item/``
   * - ``item_create``
     - ``POST /api/item/``
   * - ``item_retrieve``
     - ``GET /api/item/{id}/``
   * - ``item_update``
     - ``PUT /api/item/{id}/``
   * - ``item_partial_update``
     - ``PATCH /api/item/{id}/``
   * - ``item_destroy``
     - ``DELETE /api/item/{id}/``

**You do not add ``@extend_schema`` on these methods.**

Server setup
============

1. ``pip install --pre "djcrud[drf,mcp]"``
2. Enable ``djcrud_drf``, ``djcrud_api``, Bearer middleware, API URLs
   (:doc:`../../tutorial/drf`)
3. Register ``ModelViewSet`` subclasses on :data:`djcrud_drf.site`
4. Register permissions in ``djcrud.py``
5. Declare and register :class:`~djcrud_mcp.McpProfile` classes on
   :data:`djcrud_mcp.site` (required — see :doc:`../../tutorial/agents`)
6. Include ``djcrud_mcp.django.urls`` in project ``urlpatterns``

Client setup
============

.. list-table::
   :header-rows: 1
   :widths: 28 22 50

   * - Variable
     - Default
     - Purpose
   * - ``DJCRUD_BASE_URL``
     - ``http://127.0.0.1:8000``
     - API origin
   * - ``DJCRUD_TOKEN``
     - *(empty)*
     - Bearer token (required in production)

Aliases: ``DJMVC_*``, ``TILDETTE_*``.

Profile selection is a CLI flag, not an env var. Omit ``--registry`` to use the
host default from ``GET /api/mcp/profiles/``.

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp -mcp
   djcrud-mcp -mcp --registry articles
   djcrud-mcp --call item_list --json '{}'

Host profile API
================

When ``djcrud_mcp.django`` URLs are mounted, remote clients fetch profile
definitions over HTTP (no Django import in the MCP subprocess):

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Endpoint
     - Purpose
   * - ``GET /api/mcp/profiles/``
     - ``{"profiles": [...], "default": "<key>"}``
   * - ``GET /api/mcp/profiles/{key}/``
     - Profile JSON (instructions, ``api_prefixes``, meta)
   * - ``GET /api/mcp/viewsets/``
     - Registered ViewSet ``{model, prefix}`` list (host introspection)

MCP profiles
============

Required on the Django host: declare a class and register it on
:data:`djcrud_mcp.site` for every stdio MCP client:

.. code-block:: python

   import djcrud_mcp

   class ItemsMcp(djcrud_mcp.McpProfile):
       key = "items"
       viewsets = (ItemViewSet,)  # or models=(Item,)

   djcrud_mcp.site.register(ItemsMcp)

:meth:`~djcrud_mcp.site.McpSite.build` instantiates each registered class and
resolves ``api_prefixes`` once. ``server_name``, ``instructions``, and
``info_tool_name`` are ``@property`` defaults from the profile ``key`` and
ViewSet models unless you set class attributes to override them.

Omit ``viewsets`` / ``models`` on a profile with ``key = "default"`` to expose
every registered ``ModelViewSet``. Set ``viewsets`` / ``models`` to limit a
profile to a subset. Register multiple profiles when you run several stdio MCP
servers. You can also set ``api_prefixes`` explicitly when ViewSet introspection
is unavailable.

Custom endpoints
================

For **non-CRUD** routes (secret prompts, probes, workflow steps):

* Add a DRF :class:`~rest_framework.views.APIView` **or** ViewSet ``@action``
* Use ``@extend_schema`` so the path appears in ``/api/schema/``
* Include the ViewSet (or ``api_prefixes``) on the relevant ``McpProfile``

All MCP tools are derived from ``GET /api/schema/``. Standard list/create/update/delete
never need extra registration.

Authentication
==============

Bearer token on every tool HTTP call. Mint tokens with
:meth:`~djcrud_api.models.Token.generate` for subprocesses; ``POST /api/login/``
for local dev. See :doc:`../djcrud_api/index`.

Public API
==========

* :data:`djcrud_mcp.site` — ``register(McpProfile)``, ``build()``, ``get_profile(key)``
* :class:`~djcrud_mcp.McpProfile` — declare on the host; built on ``site.build()``;
  ``from_dict()`` for remote fetch
* ``create_mcp_server(...)``, ``fetch_schema(...)``, ``run_stdio()``
* ``discover_viewsets()`` — host-only ViewSet introspection
* ``CrudApi``, ``login()``

Further reading
===============

* :doc:`../../tutorial/agents`
* :doc:`../../design/djcrud_mcp`
* :doc:`../djcrud_drf/index`