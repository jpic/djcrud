Agents (MCP bridge)
===================

This chapter wires **stdio MCP tools** to your djcrud DRF API. Agents call
tools; ``djcrud_mcp`` translates each call into an authenticated HTTP request
against ``/api/``. Permissions are enforced on the server through the same
:func:`~djcrud.add_perm` registry as HTML and DRF.

Prerequisites: complete :doc:`routing`, :doc:`permission`, and the DRF sections
of :doc:`frontend`. Example app ``djcrud_example.mcp_example`` (planned) mirrors
this chapter.

Overview
--------

::

   Agent subprocess
        │  stdio MCP
        ▼
   djcrud-mcp  ──GET /api/schema/──►  Django
        │                              │
        └──Bearer HTTP /api/...───────►┘
                                         djcrud.permissions

Install the client extra
------------------------

On the host or sandbox where the MCP subprocess runs:

.. code-block:: bash

   pip install --pre "djcrud[mcp]"

Enable Bearer API on Django
---------------------------

Follow :doc:`frontend` through the DRF install block:

1. ``pip install --pre "djcrud[drf]"``
2. Add ``rest_framework``, ``drf_spectacular``, ``djcrud_drf``, ``djcrud_api``
   to ``INSTALLED_APPS``
3. Add Bearer middleware (before/after CSRF and session auth as documented in
   :doc:`../reference/djcrud_api/index`)
4. Merge ``djcrud_drf.site.build().urlpatterns`` in ``urls.py``
5. ``python manage.py migrate``

Tag your ViewSet
----------------

MCP discovers tools by OpenAPI **tags**, not by HTML router URL prefixes.

.. code-block:: python

   # myapp/djcrud.py
   import djcrud
   import djcrud_drf
   from drf_spectacular.utils import extend_schema

   from .models import Item

   class ItemRouter(djcrud.ModelRouter):
       model = Item

   class ItemViewSet(djcrud_drf.ModelViewSet):
       model = Item

       @extend_schema(tags=["myapp-items"], operation_id="item_list")
       def list(self, request, *args, **kwargs):
           return super().list(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_retrieve")
       def retrieve(self, request, *args, **kwargs):
           return super().retrieve(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_create")
       def create(self, request, *args, **kwargs):
           return super().create(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_update")
       def update(self, request, *args, **kwargs):
           return super().update(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_partial_update")
       def partial_update(self, request, *args, **kwargs):
           return super().partial_update(request, *args, **kwargs)

       @extend_schema(tags=["myapp-items"], operation_id="item_destroy")
       def destroy(self, request, *args, **kwargs):
           return super().destroy(request, *args, **kwargs)

   djcrud.site.routes.append(ItemRouter)

   try:
       import djcrud_drf
   except ImportError:
       djcrud_drf = None

   if djcrud_drf is not None:
       djcrud_drf.site.register(ItemViewSet)

Open permissions for agents
---------------------------

By default, only superusers pass CRUD checks. Before giving an agent a token,
register grants in ``djcrud.py`` (same chapter as :doc:`permission`):

.. code-block:: python

   import djcrud
   from djcrud.permissions import authenticated

   djcrud.add_perm(ItemRouter, "view", check=authenticated)
   djcrud.add_perm(ItemRouter, "add", check=authenticated)
   djcrud.add_perm(ItemRouter, "change", check=authenticated)
   djcrud.add_perm(ItemRouter, "delete", check=authenticated)

   def item_scoper(user, *, model, **ctx):
       return model.objects.filter(owner=user)

   djcrud.add_queryset(Item, scoper=item_scoper, router=ItemRouter)

The agent's Bearer token is tied to one Django user; queryset scoping limits
which rows appear in ``item_list`` and ``item_retrieve``.

Verify the schema
-----------------

.. code-block:: bash

   curl -s http://127.0.0.1:8000/api/schema/ \
     -H 'Accept: application/json' \
     | jq '.paths["/api/item/"]'

Confirm operations include ``tags: ["myapp-items"]`` and stable
``operationId`` values.

Obtain a token
--------------

**Development — login exchange:**

.. code-block:: bash

   curl -s -X POST http://127.0.0.1:8000/api/login/ \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"..."}' \
     | jq -r .token

**Production — server-generated token** (recommended for subprocesses):

.. code-block:: python

   from djcrud_api.models import Token

   _, raw_key = Token.generate(user=user, name="agent session")
   # Inject raw_key into subprocess env — do not pass through Celery payloads.

Define an MCP profile
---------------------

.. code-block:: python

   # myapp/mcp_profiles.py
   from djcrud_mcp import RegistryProfile

   ITEMS_PROFILE = RegistryProfile(
       key="items",
       server_name="myapp-items",
       openapi_tags=("myapp-items",),
       instructions=(
           "CRUD for Item rows. Use these tools as the canonical registry; "
           "do not store items only in chat memory."
       ),
       info_tool_name="item_registry_info",
       meta={"app": "myapp", "model": "Item"},
   )

   import djcrud_mcp
   djcrud_mcp.register_profile(ITEMS_PROFILE)

Run the MCP server
------------------

.. code-block:: bash

   export DJCRUD_BASE_URL=http://127.0.0.1:8000
   export DJCRUD_TOKEN=<raw_key>
   export DJCRUD_MCP_REGISTRY=items
   djcrud-mcp

The process speaks MCP over stdio. Configure your agent host to launch
``djcrud-mcp`` with the same environment.

One-shot tool call (debugging)
------------------------------

.. code-block:: bash

   djcrud-mcp --registry items --call item_list --json '{}'

Spawning from application code
------------------------------

When a worker or orchestrator starts an agent subprocess:

.. code-block:: python

   import os
   import subprocess

   from djcrud_api.models import Token

   _, raw_key = Token.generate(user=user, name="my agent")
   env = {
       **os.environ,
       "DJCRUD_BASE_URL": "http://127.0.0.1:8000",
       "DJCRUD_TOKEN": raw_key,
       "DJCRUD_MCP_REGISTRY": "items",
   }
   subprocess.Popen(["djcrud-mcp"], env=env, stdin=subprocess.DEVNULL)

Generate the token in trusted server code; pass only the raw key via
environment, not through the Celery message body.

Extra tools
-----------

Non-CRUD agent actions (prompt user for a secret, run a probe, begin a
workflow step) register as :class:`~djcrud_mcp.ExtraTool` handlers. Prefer
implementing the HTTP endpoint with ``@extend_schema`` first so
``/api/schema/`` stays authoritative; use ``ExtraTool`` when the MCP surface
needs richer descriptions or side effects.

See :doc:`../design/djcrud_mcp` — *Extra tools*.

Checklist
---------

.. list-table::
   :header-rows: 1
   :widths: 8 92

   * - Step
     - Done when
   * - 1
     - ``djcrud[drf]`` + ``djcrud_api`` enabled, migrations applied
   * - 2
     - ViewSet registered with ``@extend_schema(tags=..., operation_id=...)``
   * - 3
     - ``add_perm`` / ``add_queryset`` match your agent's user
   * - 4
     - ``GET /api/schema/`` lists tagged operations
   * - 5
     - Bearer token obtained and exported as ``DJCRUD_TOKEN``
   * - 6
     - ``RegistryProfile`` registered; ``djcrud-mcp`` lists expected tools
   * - 7
     - ``--call item_list`` returns scoped JSON

Next steps
----------

* :doc:`../reference/djcrud_mcp/index` — full API reference
* :doc:`../design/djcrud_mcp` — design spec and Tildette mapping
* :doc:`frontend` — OpenAPI settings and Swagger UI at ``/api/docs/``