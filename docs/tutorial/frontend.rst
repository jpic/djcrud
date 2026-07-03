Frontend (DRF API & SPAs)
=========================

This chapter covers the optional JSON API, embedding a client framework inside
djcrud's navigation shell, and generating JavaScript clients from the OpenAPI
schema. Example apps: ``drf_example`` (``Product`` router + ViewSet) and
``spa_example`` (``/spa/``).

Enable ``djcrud[drf]`` in ``djcrud_example/settings.py`` and merge API URLs in
``urls.py`` before the DRF sections below (entries are commented by default).
:func:`~djcrud.add_perm` rules from :doc:`permission` apply to HTML views and
DRF ViewSets — one ruleset for both surfaces.

DRF API
-------

Expose the same models over Django REST Framework while keeping the HTML UI from
:doc:`routing`. ``djcrud_drf`` ships with the core ``djcrud`` package; third-party
deps install via the ``[drf]`` extra.

Install
~~~~~~~

.. code-block:: bash

   pip install --pre "djcrud[drf]"

The extra pins ``djangorestframework`` and ``drf-spectacular`` to versions known
to work with djcrud. Add the apps and merge API URLs:

.. code-block:: python

   # settings.py
   INSTALLED_APPS += [
       "rest_framework",
       "drf_spectacular",
       "djcrud_drf",
   ]

.. code-block:: python

   # urls.py
   import djcrud
   import djcrud_drf

   urlpatterns = (
       djcrud.site.build().urlpatterns
       + djcrud_drf.site.build().urlpatterns
   )

Moving pieces
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Piece
     - Role
   * - :data:`djcrud_drf.site`
     - :class:`~djcrud_drf.DrfSite` at ``/api/`` — autodiscover, OpenAPI schema
   * - :meth:`djcrud_drf.site.register`
     - Registers a ViewSet on the API router
   * - :class:`~djcrud_drf.ModelViewSet`
     - CRUD ViewSet with :mod:`djcrud.permissions` registry integration
   * - :data:`djcrud_drf.router`
     - Login and token HTML routes from ``djcrud_api`` (``/api/login/``, ``/api/token/``)
   * - :data:`djcrud_drf.api`
     - DRF :class:`~rest_framework.routers.DefaultRouter` for registered ViewSets

Example app
~~~~~~~~~~~

``djcrud_example.drf_example`` registers both an HTML router and a ViewSet:

.. literalinclude:: ../../src/djcrud_example/drf_example/models.py

.. literalinclude:: ../../src/djcrud_example/drf_example/djcrud.py

The ``try``/``except`` guard lets the example project load without the ``[drf]``
extra; follow this chapter to enable DRF and uncomment the matching entries in
``djcrud_example/settings.py`` and ``djcrud_example/urls.py``.

OpenAPI
~~~~~~~

When ``drf-spectacular`` is installed:

* ``GET /api/schema/`` — OpenAPI 3 schema (CRUD ViewSets and ``POST /api/login/``)
* ``GET /api/docs/`` — Swagger UI

Configure Bearer auth for the schema (and SPA client generators below):

.. code-block:: python

   import djcrud_drf

   SPECTACULAR_SETTINGS = djcrud_drf.spectacular_settings()

.. figure:: /_static/screenshots/api-swagger-ui.png
   :alt: Swagger UI listing registered ViewSets
   :align: center
   :width: 90%

   ``/api/docs/`` after enabling ``djcrud[drf]``.

Optional Bearer token support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When API clients need Bearer authentication (HTML token UI plus ``/api/login/``),
add ``djcrud_api`` and the Bearer middleware — **not** part of the core install
(see :doc:`../install`):

.. code-block:: python

   INSTALLED_APPS += ["djcrud_api"]

   MIDDLEWARE = [
       ...
       "djcrud_api.middleware.BearerCsrfMiddleware",      # before CsrfViewMiddleware
       ...
       "djcrud_api.middleware.BearerUserMiddleware",      # after AuthenticationMiddleware
       ...
   ]

``POST /api/login/`` is a DRF view documented in the OpenAPI schema. Token
management HTML routes register on :data:`djcrud_drf.router`. See
:doc:`../reference/djcrud_api/index` for token model details.

Obtain and use a token:

.. code-block:: bash

   curl -X POST http://localhost:8000/api/login/ \
     -H 'Content-Type: application/json' \
     -d '{"username": "su", "password": "su"}'

.. code-block:: bash

   curl http://localhost:8000/api/product/ \
     -H 'Authorization: Bearer <token>'

SPA shell
---------

Build a full-screen page for a client framework (Svelte in this example) while
keeping djcrud's sidebar navigation server-rendered in HTML.

SPA template convention
~~~~~~~~~~~~~~~~~~~~~~~

Name SPA templates ``*base_spa.html`` and set ``unpoly_target = 'body'`` on the
view. Menu links on SPA pages always use ``up-follow="false"`` so every hop
reloads the full document and exits the SPA shell cleanly.

View and registration
~~~~~~~~~~~~~~~~~~~~~

Subclass :py:class:`~djcrud.views.spa.SPAView` and append it to
:data:`djcrud.site` — no model router required. Extend ``class Media`` to load
your client bundle; the shell renders ``djcrud/base_spa.html`` with sidebar
navigation and a ``#app`` mount point:

.. literalinclude:: ../../src/djcrud_example/spa_example/djcrud.py

SPA shell template
~~~~~~~~~~~~~~~~~~

:file:`djcrud/base_spa.html` renders a collapsible sidebar (``is-hidden`` by
default), introspected navigation, CSRF meta tags, and
``{{ view.media.css }}`` / ``{{ view.media.js }}`` from the view's
:class:`~django.forms.Media` — no inline JavaScript. Override
:meth:`~djcrud.views.spa.SPAView.get_mount_element` if your framework needs a
different mount node than ``#app``.

Svelte app
~~~~~~~~~~

Import ``hamburger.js`` and render the burger inside a Bulma ``.navbar`` so span
colors match the standard shell. The component toggles the server-rendered
``#sidebar``:

.. literalinclude:: ../../src/djcrud_example/spa_example/frontend/src/App.svelte

Rebuild the committed bundle after editing Svelte sources:

.. code-block:: bash

   cd src/djcrud_example/spa_example/frontend
   npm ci
   npm run build

Cross-shell navigation
~~~~~~~~~~~~~~~~~~~~~~

Standard djcrud pages swap content inside ``[up-main]``. SPA pages use a
different document shell (no top navbar). When the active view uses a
``base_spa.html`` template, :meth:`~djcrud.view.ViewMixin.unpoly_link_attributes`
returns plain links for every menu item so the browser always full-reloads.

Try it
~~~~~~

Log in and visit
`http://localhost:8000/spa/ <http://localhost:8000/spa/>`_.
Open the sidebar with the burger, then jump to ``/item/`` or other tutorial apps;
each hop reloads the matching shell.

``SpaView`` is tagged with ``navigation`` so it appears in the standard sidebar
too — useful for entering the SPA from a normal page.

SPA client codegen
------------------

Call your DRF endpoints from the SPA without hand-writing fetch wrappers.
``GET /api/schema/`` describes login and every registered ViewSet — use it as
the single contract for Swagger, Postman, and JavaScript clients.

Export the schema
~~~~~~~~~~~~~~~~~

Offline — no running server:

.. code-block:: bash

   python manage.py spectacular --file openapi.json --format openapi-json

From the SPA frontend package:

.. code-block:: bash

   cd src/djcrud_example/spa_example/frontend
   npm run api:schema

Generate the JavaScript client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The example uses `OpenAPI Generator <https://openapi-generator.tech/>`_ with
the ``javascript`` target (fetch + promises):

.. code-block:: bash

   cd src/djcrud_example/spa_example/frontend
   npm run api:generate

Both steps: ``npm run api``. The generated ``src/api/`` tree is gitignored;
regenerate after model or ViewSet changes.

Example usage
~~~~~~~~~~~~~

.. code-block:: javascript

   import { AuthApi, ProductApi } from "./api/src/index.js";
   import { ApiClient } from "./api/src/ApiClient.js";

   const client = new ApiClient("/api");
   const auth = new AuthApi(client);
   const { token } = await auth.apiLogin({ username: "su", password: "su" });
   client.authentications.BearerAuth.accessToken = token;

   const products = new ProductApi(client);
   const list = await products.productList();

When the user is already logged in via the HTML session (as on ``/spa/``), you
can also call ``/api/product/`` with ``credentials: 'same-origin'`` — see
``spa_example/frontend/src/App.svelte``.

Alternative generators
~~~~~~~~~~~~~~~~~~~~~~

Any OpenAPI 3 toolchain works against ``/api/schema/``. Popular choices:

* `@hey-api/openapi-ts` — fetch-native, pairs well with Vite
* `orval` — hooks and functions (often TypeScript)

Pick one generator; djcrud maintains the schema, not the client output.

Reference
---------

* :doc:`../reference/djcrud_drf/index` — ViewSet API surface and ``spectacular_settings()``
* :doc:`../reference/djcrud_api/index` — Bearer tokens and ``POST /api/login/``
* :doc:`agents` — stdio MCP tools from the same OpenAPI schema
* :doc:`../reference/djcrud_mcp/index` — MCP bridge reference

Tests
-----

* `tests/test_drf.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_drf.py>`_
* `tests/test_spa_example.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_spa_example.py>`_
* Browser tests in :file:`tests/test_spa_browser.py` verify full-page transitions
  between the standard shell and the SPA.
