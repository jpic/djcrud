djcrud_mcp
~~~~~~~~~~

Django **host** package for MCP profile registration. Ships inside the ``djcrud``
wheel (requires :doc:`../djcrud_drf/index`). Stdio MCP / FastMCP lives in the
separate ``djcrud-client`` package — not here.

.. code-block:: bash

   pip install --pre "djcrud[drf,mcp]"

``djcrud[mcp]`` also pulls ``djcrud-client`` for agent subprocesses. See
:doc:`../../tutorial/agents`.

Design spec: :doc:`../../design/djcrud_mcp`.

Server setup
============

1. ``pip install --pre "djcrud[drf,mcp]"``
2. Enable ``djcrud_drf``, ``djcrud_api``, Bearer middleware, API URLs
   (:doc:`../../tutorial/drf`)
3. Register ``ModelViewSet`` subclasses on :data:`djcrud_drf.site`
4. Register permissions in ``djcrud.py``
5. Declare and register :class:`~djcrud_mcp.McpProfile` classes on
   :data:`djcrud_mcp.site` (required — see :doc:`../../tutorial/agents`)
6. Add ``djcrud_mcp`` to ``INSTALLED_APPS`` and include :data:`djcrud_drf.site`
   URLs — profile API ViewSets register from :file:`djcrud_mcp/djcrud.py`` via
   autodiscovery at ``/api/mcp/``

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "djcrud_drf",
       "djcrud_mcp",
   ]

   urlpatterns = [
       # ...
   ] + djcrud.site.build().urlpatterns + djcrud_drf.site.build().urlpatterns

MCP profiles
============

.. code-block:: python

   import djcrud_mcp

   class ItemsMcp(djcrud_mcp.McpProfile):
       key = "items"
       viewsets = (ItemViewSet,)

   djcrud_mcp.site.register(ItemsMcp)

:meth:`~djcrud_mcp.site.McpSite.build` instantiates each registered class and
resolves ``api_prefixes``. ``server_name``, ``instructions``, and
``info_tool_name`` are ``@property`` defaults from the profile ``key`` and
ViewSet models unless you override class attributes.

Host profile API
================

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
     - Registered ViewSet ``{model, prefix}`` list

Public API
==========

* :data:`djcrud_mcp.site` — ``register(McpProfile)``, ``build()``, ``get_profile(key)``
* :class:`~djcrud_mcp.McpProfile` — declare on the host; built on ``site.build()``
* ``discover_viewsets()``, ``api_path_for()``, ``model_name_for()``

Client (``djcrud-client``)
==========================

Remote stdio MCP subprocesses install ``djcrud-client`` only (``mcp`` + ``httpx``,
no Django). FastMCP, schema tool building, and HTTP proxying live in
:mod:`djcrud_client`.

.. code-block:: bash

   pip install djcrud-client
   export DJCRUD_TOKEN=<raw_key>
   djcrud-client -mcp
   djcrud-client -mcp --registry articles
   djcrud-client --call item_list --json '{}'

Further reading
===============

* :doc:`../../tutorial/agents`
* :doc:`../../design/djcrud_mcp`
* :doc:`../djcrud_drf/index`