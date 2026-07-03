DRF API
=======

This chapter covers the optional JSON API over Django REST Framework.
Example app: ``drf_example`` (``Product`` and ``Article`` ViewSets at ``/api/``).

Enable ``djcrud[drf]``, add the DRF apps to ``INSTALLED_APPS``, and merge API
URLs in ``urls.py``. :func:`~djcrud.permissions.add_perm` rules
from :doc:`permission` apply to HTML views and DRF ViewSets — one ruleset for
both surfaces.

HTML CRUD is covered in :doc:`routing`; this chapter is API-only.
``djcrud_drf`` ships with the core ``djcrud`` package; third-party deps install
via the ``[drf]`` extra.

With ``django.contrib.admin`` installed (and optionally ``djcrud_history``),
:class:`~djcrud_drf.ModelViewSet` writes ``LogEntry`` rows on create, update,
and delete — the same audit trail as HTML CRUD. Entries appear on each model's
history view with no extra ViewSet code. Set ``log_actions = False`` on a
ViewSet to disable logging.

Install
-------

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
       "djcrud_example.drf_example",  # tutorial app; use your own app in production
   ]

.. code-block:: python

   # urls.py
   import djcrud
   import djcrud_drf

   urlpatterns = (
       djcrud.site.build().urlpatterns
       + djcrud_drf.site.build().urlpatterns
   )

Define a :class:`~djcrud_drf.ModelViewSet`
------------------------------------------

Subclass :class:`~djcrud_drf.ModelViewSet`, set ``model``, and register on
:data:`djcrud_drf.site` from the app's ``djcrud.py`` module (autoloaded by
:meth:`djcrud.Site.build`):

.. code-block:: python

   import djcrud_drf
   from .models import Product

   class ProductViewSet(djcrud_drf.ModelViewSet):
       model = Product

   djcrud_drf.site.register(ProductViewSet)

That is the full CRUD setup — list, create, retrieve, update, and destroy at
``/api/product/`` with permissions from :func:`~djcrud.permissions.add_perm` on the same
model.

Custom actions use ``@action`` on the ViewSet; register permission rules with
:func:`~djcrud.permissions.add_perm` using the action name as the shortcode (see
``publish`` below).

Example app
-----------

``djcrud_example.drf_example`` registers ``ProductViewSet`` and ``ArticleViewSet``
in ``djcrud.py``. :meth:`djcrud.Site.build` imports that module;
:meth:`djcrud_drf.DrfSite.build` wires the ViewSets at ``/api/``:

.. literalinclude:: ../../src/djcrud_example/drf_example/djcrud.py

Uncomment the DRF URL merge in ``djcrud_example/urls.py`` when running the
example project locally.

Moving pieces
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Piece
     - Role
   * - :data:`djcrud_drf.site`
     - :class:`~djcrud_drf.DrfSite` at ``/api/`` — OpenAPI schema and ViewSet routes
   * - :meth:`djcrud_drf.site.register`
     - Registers a ViewSet on the API router
   * - :class:`~djcrud_drf.ModelViewSet`
     - CRUD ViewSet with :mod:`djcrud.permissions` registry integration
   * - :data:`djcrud_drf.router`
     - Login and token HTML routes from ``djcrud_api`` (``/api/login/``, ``/api/token/``)
   * - :data:`djcrud_drf.api`
     - DRF :class:`~rest_framework.routers.DefaultRouter` for registered ViewSets

OpenAPI
-------

When ``drf-spectacular`` is installed:

* ``GET /api/schema/`` — OpenAPI 3 schema (CRUD ViewSets and ``POST /api/login/``)
* ``GET /api/docs/`` — Swagger UI

Configure Bearer auth for the schema (and SPA client generators in :doc:`spa`):

.. code-block:: python

   import djcrud_drf

   SPECTACULAR_SETTINGS = djcrud_drf.spectacular_settings()

.. figure:: /_static/screenshots/api-swagger-ui.png
   :alt: Swagger UI listing registered ViewSets
   :align: center
   :width: 90%

   ``/api/docs/`` after enabling ``djcrud[drf]``.

Optional Bearer token support
-----------------------------

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

Reference
---------

* :doc:`../reference/djcrud_drf/index` — ViewSet API surface and ``spectacular_settings()``
* :doc:`../reference/djcrud_api/index` — Bearer tokens and ``POST /api/login/``
* :doc:`agents` — stdio MCP tools from the same OpenAPI schema
* :doc:`../reference/djcrud_mcp/index` — MCP bridge reference
* :doc:`spa` — SPA shell and OpenAPI client codegen

Tests
-----

* `tests/test_drf.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_drf.py>`_