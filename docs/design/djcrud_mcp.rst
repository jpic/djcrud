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
* **Host-owned profiles** — ``McpProfile`` classes register on
  :data:`djcrud_mcp.site`; remote clients fetch ``GET /api/mcp/profiles/{key}/``.

Non-goals
---------

* User MCP server vaults (application code, e.g. Tildette ``djacp_mcp``).
* Django URL routes for MCP stdio transport.
* Re-declaring permissions in the MCP client.
* Client-side tool definitions outside OpenAPI schema.

Architecture
------------

::

   ┌──────────────────┐     stdio MCP      ┌─────────────────────┐
   │ Agent            │ ◄────────────────► │ djcrud_mcp          │
   └──────────────────┘                    └──────────┬──────────┘
                                                      │
              GET /api/mcp/profiles/{key}/  +  GET /api/schema/
              Bearer HTTP /api/<model>/
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

1. **Registered ViewSets** — on the Django host, introspect
   :data:`djcrud_drf.site` to learn each model's API path:
   ``/api/{model.__name__.lower()}/``.
2. **Schema fetch** — ``GET /api/schema/``; keep operations whose path matches
   a profile's ViewSet prefixes.
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
   import djcrud_drf

   djcrud.site.routes.append(ItemRouter)
   djcrud.add_perm(ItemRouter, "view,add,change,delete", check=djcrud.authenticated)
   djcrud_drf.site.register(ItemViewSet)

That is the full MCP CRUD setup. Custom ``@action`` methods use the method name
as the permission shortcode (``publish`` → ``publish`` rule).

MCP profiles (optional grouping)
--------------------------------

When one stdio MCP server should expose **a subset** of registered ViewSets
(e.g. tasks vs admin models), declare a :class:`~djcrud_mcp.McpProfile` on the
Django host and register it on :data:`djcrud_mcp.site`:

.. code-block:: python

   import djcrud_mcp

   class ItemsMcp(djcrud_mcp.McpProfile):
       key = "items"
       server_name = "myapp-items"
       viewsets = (ItemViewSet,)   # or models=(Item,)
       instructions = "..."
       info_tool_name = "item_registry_info"

   djcrud_mcp.site.register(ItemsMcp)

Default profile: **all** ``ModelViewSet`` registrations on
:data:`djcrud_drf.site` (synthesized when no explicit ``default`` profile is
registered).

Remote MCP subprocesses fetch the built profile from
``GET /api/mcp/profiles/{key}/`` — they do not import Django or declare
profiles locally.

Custom (non-CRUD) endpoints
---------------------------

Only non-standard routes need explicit schema surfacing:

* Standalone :class:`~rest_framework.views.APIView` (workflow steps, probes)
* ``@action`` on a ViewSet for one-off operations

Use ``@extend_schema`` so the path appears in ``/api/schema/``, then include the
ViewSet (or ``api_prefixes``) on the relevant ``McpProfile``. There is no
parallel client-side tool registry — schema is the single source of truth.

Authentication
--------------

Same as :doc:`../reference/djcrud_api/index`:

* Subprocess: ``DJCRUD_TOKEN`` in env (host calls ``Token.generate``)
* Dev CLI: ``POST /api/login/`` or ``--user`` / ``--password``

Passwords are never sent per tool call.

Package layout
--------------

::

   djcrud-mcp/src/djcrud_mcp/
     site.py        # McpSite — register(McpProfile), build profiles
     profiles.py    # McpProfile, RegistryProfile
     django/        # GET /api/mcp/profiles/ (host only)
     viewsets.py    # discover registered ModelViewSets, api_path_for(model)
     schema.py      # filter schema paths by profile prefixes
     tools.py       # tool_name(model, action), render_path, split_arguments
     server.py      # create_mcp_server()
     api.py         # CrudApi, fetch_profile()
     config.py

Application example (Tildette)
------------------------------

Tildette declares two host profiles — ``tasks`` and ``mcp`` — in
``tildette_tasks/mcp_profile.py`` and ``tildette_mcp/mcp_profile.py``, each
registered with ``djcrud_mcp.site.register(...)``. The sandbox
``tildette-client`` subprocess fetches them over HTTP; it does not ship profile
definitions in the workspace package.

Related docs
------------

* :doc:`../reference/djcrud_mcp/index`
* :doc:`../tutorial/agents`
* :doc:`../reference/djcrud_drf/index`
* :doc:`../philosophy`