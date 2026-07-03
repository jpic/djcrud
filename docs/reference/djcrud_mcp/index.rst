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

Register a ViewSet the same way as :doc:`../../tutorial/frontend` — MCP picks
it up automatically:

.. code-block:: python

   # djcrud.py
   djcrud.site.routes.append(ItemRouter)
   djcrud.add_perm(ItemRouter, "view,add,change,delete", check=authenticated)

   # djcrud_drf.py
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

1. ``pip install --pre "djcrud[drf]"``
2. Enable ``djcrud_drf``, ``djcrud_api``, Bearer middleware, API URLs
   (:doc:`../../tutorial/frontend`)
3. Register ``ModelViewSet`` subclasses on :data:`djcrud_drf.site`
4. Register permissions in ``djcrud.py``

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
   * - ``DJCRUD_MCP_REGISTRY``
     - ``default``
     - Profile key

Aliases: ``DJMVC_*``, ``TILDETTE_*``.

.. code-block:: bash

   export DJCRUD_TOKEN=<raw_key>
   djcrud-mcp
   djcrud-mcp --call item_list --json '{}'

Registry profiles
=================

Optional: limit which registered ViewSets one MCP server exposes.

.. code-block:: python

   RegistryProfile(
       key="items",
       server_name="myapp-items",
       viewsets=(ItemViewSet,),  # or models=(Item,)
       instructions="CRUD for Item via the JSON API.",
       info_tool_name="item_registry_info",
   )

Omit ``viewsets`` / ``models`` to expose every registered ``ModelViewSet``.

Custom endpoints only
=====================

For **non-CRUD** routes (secret prompts, probes, workflow steps):

* Add a DRF :class:`~rest_framework.views.APIView` **or** ViewSet ``@action``
* Use ``@extend_schema`` so the path appears in ``/api/schema/``, **or**
* Register :class:`~djcrud_mcp.ExtraTool` on the profile

Standard list/create/update/delete never need this.

Authentication
==============

Bearer token on every tool HTTP call. Mint tokens with
:meth:`~djcrud_api.models.Token.generate` for subprocesses; ``POST /api/login/``
for local dev. See :doc:`../djcrud_api/index`.

Public API (planned)
====================

* ``create_mcp_server(...)``
* ``RegistryProfile`` — ``viewsets`` / ``models`` filter
* ``register_profile(profile)``
* ``discover_viewsets()`` — registered ``ModelViewSet`` → API path map
* ``build_tools_from_schema(schema, viewsets)``
* ``CrudApi``, ``ExtraTool``

Further reading
===============

* :doc:`../../tutorial/agents`
* :doc:`../../design/djcrud_mcp`
* :doc:`../djcrud_drf/index`