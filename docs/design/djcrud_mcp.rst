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

* **Register once** — ``djcrud_drf.site.register(ItemViewSet)`` for HTML/DRF, plus
  ``djcrud_mcp.site.register(ItemMcp)`` listing that ViewSet (or ``key =
  "default"`` with no filter) for MCP.
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
   │ Agent            │ ◄────────────────► │ djcrud_client       │
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

MCP profiles
------------

Declare a :class:`~djcrud_mcp.McpProfile` on the Django host and register it on
:data:`djcrud_mcp.site`. Registration is required for every stdio MCP client —
remote subprocesses fetch the built profile over HTTP and never synthesize one
locally:

.. code-block:: python

   import djcrud_mcp

   class ExampleMcp(djcrud_mcp.McpProfile):
       viewsets = (ItemViewSet,)   # or models=(Item,)

   djcrud_mcp.site.register(ExampleMcp)

Profile build lifecycle
~~~~~~~~~~~~~~~~~~~~~~~

Same model as HTML routes and DRF ViewSets:

1. **Declare** — class attributes on ``McpProfile`` (``key``, ``viewsets``, optional
   overrides).
2. **Register** — ``djcrud_mcp.site.register(ExampleMcp)`` stores the class.
3. **Build** — ``site.build()`` calls ``ExampleMcp().build()``, resolving ViewSet
   prefixes once and caching them on the instance.
4. **Serve** — ``GET /api/mcp/profiles/{key}/`` returns ``profile.to_dict()`` for
   remote ``djcrud-client`` subprocesses.

Computed fields (``@property`` unless overridden on the class):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Field
     - Default rule
   * - ``server_name``
     - ``{host-slug}-{key}`` from ``ROOT_URLCONF`` (e.g. ``myapp-items``)
   * - ``info_tool_name``
     - ``{primary_model}_registry_info``
   * - ``instructions``
     - ``CRUD for {models} via the JSON API.``
   * - ``api_prefixes``
     - Derived from registered ViewSets at build time
   * - ``meta["name"]``
     - Same as ``server_name``

Register one profile per project. Set ``viewsets`` / ``models`` to list the API
surfaces agents may call.

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

Host package (``djcrud`` wheel, ``src/djcrud_mcp/``):

::

   src/djcrud_mcp/
     site.py          # McpSite — register(McpProfile), build profiles
     profiles.py      # McpProfile (instances built on site.build())
     api_viewsets.py  # GET /api/mcp/profiles/ (host only)
     viewsets.py      # discover registered ModelViewSets, api_path_for(model)

Client package (``djcrud-client``, no Django):

::

   djcrud-client/src/djcrud_client/
     profile.py       # fetch profile JSON from host
     schema.py        # filter schema paths by profile prefixes
     tools.py         # tool_name(model, action), render_path, split_arguments
     server.py        # create_mcp_server()
     api.py           # CrudApi, fetch_profile()
     config.py

Related docs
------------

* :doc:`../reference/djcrud_mcp/index`
* :doc:`../tutorial/agents`
* :doc:`../reference/djcrud_drf/index`
* :doc:`../philosophy`