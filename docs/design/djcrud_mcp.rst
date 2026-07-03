djcrud_mcp design
=================

This document is the implementation spec for :doc:`../reference/djcrud_mcp/index`.
Read it before writing code or the :doc:`../tutorial/agents` walkthrough.

Problem
-------

Agents (LLM subprocesses, IDE plugins, automation runners) need **machine CRUD**
without a hand-written SDK for every model. djcrud already emits an OpenAPI
schema from :doc:`../reference/djcrud_drf/index` at ``GET /api/schema/``.
``djcrud_mcp`` turns that schema into **stdio MCP tools** that proxy
authenticated HTTP calls back to the same DRF endpoints humans reach through the
browser or ``curl``.

Goals
-----

* **One permission registry** — MCP is another client surface; rules registered
  with :func:`~djcrud.add_perm` and :func:`~djcrud.add_queryset` in ``djcrud.py``
  apply on the server when the token hits a ViewSet. No parallel auth stack.
* **Schema-driven tools** — discover operations from OpenAPI; avoid hard-coded
  URL prefixes per application.
* **Stable tool names** — use ``operationId`` from the schema so agent prompts
  survive URL layout changes.
* **Thin subprocess** — no Django ORM in the MCP bridge; only ``httpx`` and
  ``mcp``.

Non-goals
---------

* **Host-side MCP registry** — storing user MCP server configs, secret vaults,
  probe/render pipelines (application-specific; see Tildette ``djacp_mcp``).
* **Django URL routes for MCP** — transport is stdio between agent and
  subprocess, not HTTP into Django.
* **Sandbox / gVisor spawn** — how the host starts the subprocess is an
  application concern.

Architecture
------------

::

   ┌──────────────────┐     stdio MCP      ┌─────────────────────┐
   │ Agent (Claude,   │ ◄────────────────► │ djcrud_mcp          │
   │ Grok, Cursor, …) │                    │ (FastMCP subprocess)│
   └──────────────────┘                    └──────────┬──────────┘
                                                      │ HTTP Bearer
                                                      ▼
                                           ┌─────────────────────┐
                                           │ Django + djcrud_drf │
                                           │ GET /api/schema/    │
                                           │ CRUD /api/<model>/  │
                                           └──────────┬──────────┘
                                                      │
                                                      ▼
                                           ┌─────────────────────┐
                                           │ djcrud.permissions  │
                                           │ registry            │
                                           └─────────────────────┘

On startup the bridge:

1. Fetches ``GET /api/schema/`` (OpenAPI 3 JSON).
2. Selects operations whose ``tags`` match a :class:`~djcrud_mcp.RegistryProfile`.
3. Registers one MCP tool per operation (name from ``operationId``).
4. On tool call, issues ``Authorization: Bearer <token>`` to the matching path.

Authentication
--------------

MCP tools never send a password. Two ways to obtain a Bearer token:

**Environment (production path for subprocesses)**

The host generates or reuses a token and injects it before ``Popen``:

.. code-block:: bash

   export DJCRUD_BASE_URL=http://127.0.0.1:8000
   export DJCRUD_TOKEN=<raw_key>

Compatibility aliases (documented, not primary):

* ``DJMVC_BASE_URL`` / ``DJMVC_TOKEN`` — legacy djmvc naming
* ``TILDETTE_BASE_URL`` / ``TILDETTE_TOKEN`` — Tildette deployments

**Login exchange (development / CLI)**

When no token env is set, the console entry may call:

.. code-block:: http

   POST /api/login/
   Content-Type: application/json

   {"username": "...", "password": "..."}

Response (1-hour token by default):

.. code-block:: json

   {"token": "...", "expires": "...", "prefix": "..."}

See :doc:`../reference/djcrud_api/index` for token storage and middleware.

Server-side token minting (recommended for agents):

.. code-block:: python

   from djcrud_api.models import Token

   _, raw_key = Token.generate(user=user, name="agent session")
   # Pass raw_key to subprocess env — never enqueue in Celery messages.

Permissions
-----------

The MCP bridge **does not** re-implement permission checks. Each HTTP call
carries a Bearer token; Django middleware sets ``request.user``; DRF ViewSets
call the same registry as HTML views.

Implications for application authors:

* Register ``add_perm`` / ``add_queryset`` before exposing a ViewSet to agents.
* Scoped querysets return 404 for out-of-scope PKs — same as the HTML UI.
* A token always maps to **one user** — design agent tokens per thread owner,
  not shared service accounts, unless intentional.

Tool discovery
--------------

Legacy clients (Tildette ``tildette_client``) filter schema ``paths`` by URL
prefix (``/taskssection``, ``/mcpsection``). That couples tool sets to djcrud
HTML section layout.

**djcrud_mcp uses OpenAPI tags.**

Tag every DRF endpoint that should appear in a given MCP server:

.. code-block:: python

   from drf_spectacular.utils import extend_schema

   class ItemViewSet(djcrud_drf.ModelViewSet):
       model = Item

       @extend_schema(tags=["myapp-items"], operation_id="item_list")
       def list(self, request, *args, **kwargs):
           return super().list(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_create")
       def create(self, request, *args, **kwargs):
           return super().create(request, *args, **kwargs)

Custom :class:`~rest_framework.views.APIView` routes follow the same pattern.

**Registry profiles** map MCP server names to tag sets:

.. code-block:: python

   RegistryProfile(
       key="items",
       server_name="myapp-items",
       openapi_tags=("myapp-items",),
       instructions="CRUD for Item rows via the JSON API.",
       info_tool_name="item_registry_info",
   )

``filter_operations(schema, tags=profile.openapi_tags)`` returns matching
``(path, method, operation)`` triples.

Tool naming
-----------

Primary: ``operation["operationId"]`` from the schema.

Fallback (when ``operationId`` is missing): path-heuristic naming compatible with
legacy ``tildette_client.tools.tool_name_for_operation`` so migrations can
compare old and new tool sets.

Every profile exposes a **registry info** meta-tool (``info_tool_name``) returning
JSON metadata (capabilities, setup hints) for the agent system prompt.

Extra tools
-----------

Not every agent action is model CRUD. Applications register
:class:`~djcrud_mcp.ExtraTool` handlers alongside schema-derived tools:

* Secret prompts, config render, health probes, turn lifecycle, etc.
* Implemented as Python callables with explicit ``name`` and ``description``.
* Should still call HTTP endpoints that are **also** in the schema when possible,
  so ``/api/schema/`` remains the discovery source of truth.

Tildette's ``_register_mcp_secret_tools()`` becomes ``ExtraTool`` registrations
in a Tildette-specific profile module — not part of generic ``djcrud_mcp``.

Package layout (planned)
------------------------

::

   src/djcrud_mcp/
     __init__.py      # create_mcp_server, RegistryProfile, register_profile
     __main__.py      # djcrud-mcp console script
     api.py           # CrudApi, login()
     config.py        # env: base URL, token, registry key
     schema.py        # filter_operations, build_tools
     tools.py         # render_path, split_arguments, tool naming
     profiles.py      # RegistryProfile, get_profile, REGISTRIES
     server.py        # create_mcp_server()
     extras.py        # ExtraTool

Optional Django app (``apps.py``) for server-side profile autodiscover is **v2**.
v1 keeps profiles in the subprocess (env ``DJCRUD_MCP_REGISTRY`` or CLI
``--registry``).

Distribution
------------

* Same ``djcrud`` wheel as core and ``djcrud_drf``.
* Optional extra: ``pip install "djcrud[mcp]"`` → ``mcp``, ``httpx``.
* Console script: ``djcrud-mcp`` (stdio server) and ``djcrud-mcp --call``.

Server prerequisites
--------------------

On the Django host:

1. ``pip install "djcrud[drf]"`` — DRF + drf-spectacular.
2. ``djcrud_api`` in ``INSTALLED_APPS`` + Bearer middleware.
3. ViewSets registered on :data:`djcrud_drf.site` with ``@extend_schema`` tags.
4. Permission rules in ``djcrud.py``.

Client prerequisites
--------------------

On the machine or sandbox running the MCP subprocess:

1. ``pip install "djcrud[mcp]"`` (or inherit from application image).
2. ``DJCRUD_TOKEN`` and ``DJCRUD_BASE_URL`` in the environment.
3. ``djcrud-mcp`` or application wrapper (e.g. ``tildette-client``) on ``PATH``.

Tildette mapping
----------------

When Tildette adopts ``djcrud_mcp``, ``tildette_client`` becomes a thin profile
layer:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - tildette_client today
     - djcrud_mcp target
   * - ``filter_paths(controller_prefix)``
     - ``filter_operations(openapi_tags)``
   * - ``tool_name_for_operation()`` heuristics
     - ``operationId`` primary
   * - ``TildetteApi``
     - ``CrudApi``
   * - ``TASKS_PROFILE``, ``MCP_PROFILE``
     - Tildette ``profiles.py`` registering into ``djcrud_mcp``
   * - ``_register_mcp_secret_tools()``
     - ``ExtraTool`` list on MCP profile
   * - ``tildette-client`` entry point
     - imports ``djcrud_mcp``, adds Tildette profiles

Sandbox spawn (``tildette_process.tasks.agent``, ``tildette_acp.mcp``) stays in
Tildette; it only changes imports and env var names.

OpenAPI request bodies
----------------------

drf-spectacular emits OpenAPI 3 ``requestBody`` (not Swagger 2 ``in: body``
parameters). ``split_arguments()`` must read both shapes so tool input schemas
stay accurate.

Related docs
------------

* :doc:`../reference/djcrud_mcp/index` — install and public API
* :doc:`../tutorial/agents` — hands-on walkthrough
* :doc:`../reference/djcrud_drf/index` — ViewSets and schema
* :doc:`../reference/djcrud_api/index` — Bearer tokens
* :doc:`../philosophy` — one registry, every surface