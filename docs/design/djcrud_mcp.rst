djcrud_mcp design
=================

This document is the implementation spec for :doc:`../reference/djcrud_mcp/index`.
Read it before writing code or the :doc:`../tutorial/agents` walkthrough.

Problem
-------

Agents need machine CRUD without a hand-written SDK. djcrud already exposes
:class:`~djcrud_drf.ModelViewSet` on ``/api/<model>/`` with the same
:mod:`djcrud.permissions` registry as HTML. ``djcrud_mcp`` turns those
**registered ViewSets** into stdio MCP tools — no per-action decorators.

Goals
-----

* **Register once** — ``djcrud_drf.site.register(ItemViewSet)`` is enough for
  HTML *and* MCP, same as today for HTML + DRF.
* **Permissions on the server** — :class:`~djcrud_drf.ModelViewSet` already
  calls :func:`~djcrud.has_permission` and :func:`~djcrud.get_queryset`; the MCP
  bridge is a Bearer HTTP proxy.
* **Automatic tool names** — ``{model}_{action}`` (e.g. ``item_list``,
  ``item_create``) derived from the ViewSet model and DRF action, matching
  :data:`~djcrud_drf.viewsets.ACTION_SHORTCODES` semantics.
* **No ``@extend_schema`` on CRUD** — drf-spectacular already documents
  registered ViewSets; MCP reads ``GET /api/schema/`` and filters by known API
  paths.

Non-goals
---------

* Host-side MCP registry (user server vaults — application code, e.g. Tildette
  ``djacp_mcp``).
* Django URL routes for MCP stdio transport.
* Re-declaring permissions in the MCP client.

Architecture
------------

::

   ┌──────────────────┐     stdio MCP      ┌─────────────────────┐
   │ Agent            │ ◄────────────────► │ djcrud_mcp          │
   └──────────────────┘                    └──────────┬──────────┘
                                                      │
                        GET /api/schema/  +  Bearer HTTP /api/<model>/
                                                      ▼
                                           ┌─────────────────────┐
                                           │ djcrud_drf          │
                                           │ ModelViewSet        │
                                           └──────────┬──────────┘
                                                      ▼
                                           ┌─────────────────────┐
                                           │ djcrud.permissions  │
                                           └─────────────────────┘

CRUD discovery (default)
------------------------

1. **Registered ViewSets** — introspect :data:`djcrud_drf.site` (same registry
   as URL building) to learn each model's API path:
   ``/api/{model.__name__.lower()}/``.
2. **Schema fetch** — ``GET /api/schema/``; keep operations whose path matches
   a registered ViewSet prefix.
3. **Tool naming** — for each standard DRF action on that path:

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - HTTP
        - DRF action
        - MCP tool name
      * - ``GET /api/item/``
        - list
        - ``item_list``
      * - ``POST /api/item/``
        - create
        - ``item_create``
      * - ``GET /api/item/{id}/``
        - retrieve
        - ``item_retrieve``
      * - ``PUT /api/item/{id}/``
        - update
        - ``item_update``
      * - ``PATCH /api/item/{id}/``
        - partial_update
        - ``item_partial_update``
      * - ``DELETE /api/item/{id}/``
        - destroy
        - ``item_destroy``

   Naming uses the model's lowercase name (same rule as
   :meth:`~djcrud_drf.ModelViewSet.build_router`).

4. **Permissions** — no client-side gate. The token's user hits
   ``ModelViewSet.check_permissions`` / ``check_object_permissions``; denied
   actions return 403 over HTTP.

**Application code for CRUD:**

.. code-block:: python

   # djcrud.py
   djcrud.site.routes.append(ItemRouter)
   djcrud.add_perm(ItemRouter, "view,add,change,delete", check=djcrud.authenticated)

   # djcrud_drf.py
   djcrud_drf.site.register(ItemViewSet)

That is the full MCP CRUD setup. Custom ``@action`` methods use the method name
as the permission shortcode (``publish`` → ``publish`` rule).

Registry profiles (optional grouping)
-------------------------------------

When one MCP server should expose **a subset** of registered ViewSets (e.g.
tasks vs admin models), a :class:`~djcrud_mcp.RegistryProfile` lists **models
or ViewSet classes** — not OpenAPI tags:

.. code-block:: python

   RegistryProfile(
       key="items",
       server_name="myapp-items",
       viewsets=(ItemViewSet,),   # or models=(Item,)
       instructions="...",
       info_tool_name="item_registry_info",
   )

Default profile: **all** ``ModelViewSet`` registrations on
:data:`djcrud_drf.site`.

Custom (non-CRUD) endpoints
---------------------------

Only non-standard routes need explicit schema surfacing:

* Standalone :class:`~rest_framework.views.APIView` (workflow steps, probes)
* ``@action`` on a ViewSet for one-off operations

Use ``@extend_schema`` (or :class:`~djcrud_mcp.ExtraTool`) **only** for these.
Register them on the profile's ``extra_tools`` list or a dedicated custom
APIView with a documented path under ``/api/``.

Authentication
--------------

Same as :doc:`../reference/djcrud_api/index`:

* Subprocess: ``DJCRUD_TOKEN`` in env (host calls ``Token.generate``)
* Dev CLI: ``POST /api/login/`` or ``--user`` / ``--password``

Passwords are never sent per tool call.

Package layout (planned)
------------------------

::

   src/djcrud_mcp/
     viewsets.py    # discover registered ModelViewSets, api_path_for(model)
     schema.py      # filter schema paths by registered prefixes
     tools.py       # tool_name(model, action), render_path, split_arguments
     server.py      # create_mcp_server()
     profiles.py    # RegistryProfile(viewsets=..., models=...)
     api.py         # CrudApi
     config.py
     extras.py      # ExtraTool for non-CRUD only

Tildette mapping
----------------

Replace URL-prefix filtering (``/taskssection``) with ViewSet/model-based
discovery after DRF migration:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - tildette_client today
     - djcrud_mcp
   * - ``controller_prefix="/taskssection"``
     - ``models=(Task,)`` or ``viewsets=(TaskViewSet,)``
   * - ``tool_name_for_operation()`` path heuristics
     - ``{model}_{action}`` from registered ViewSet
   * - ``_register_mcp_secret_tools()``
     - ``ExtraTool`` only (non-CRUD)

Related docs
------------

* :doc:`../reference/djcrud_mcp/index`
* :doc:`../tutorial/agents`
* :doc:`../reference/djcrud_drf/index`
* :doc:`../philosophy`