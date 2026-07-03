djcrud_drf
~~~~~~~~~~

Optional DRF API layer for djcrud. Install separately — core djcrud has **no**
DRF dependency.

Install
=======

.. code-block:: bash

   pip install --pre "djcrud[drf]"

Add to ``INSTALLED_APPS`` and include API URLs:

.. code-block:: python

   INSTALLED_APPS += [
       "rest_framework",
       "drf_spectacular",
       "djcrud_drf",
   ]

   # urls.py
   import djcrud_drf
   urlpatterns = (
       djcrud.site.build().urlpatterns
       + djcrud_drf.site.build().urlpatterns
   )

Register in each app's ``djcrud.py`` (with HTML router):

.. code-block:: python

   import djcrud
   import djcrud_drf
   from .models import Item

   class ItemRouter(djcrud.ModelRouter):
       model = Item

   class ItemViewSet(djcrud_drf.ModelViewSet):
       model = Item

   djcrud.site.routes.append(ItemRouter)
   djcrud_drf.site.register(ItemViewSet)

Permissions
===========

:func:`~djcrud.add_perm` and :func:`~djcrud.add_queryset` registered in each
app's ``djcrud.py`` apply to HTML views and DRF ViewSets for that app. See
:mod:`djcrud.permissions`.

OpenAPI
=======

When ``drf-spectacular`` is installed:

* ``GET /api/schema/`` — OpenAPI 3 schema
* ``GET /api/docs/`` — Swagger UI

The schema includes ``POST /api/login/`` (Bearer token exchange) and CRUD routes
for every registered :class:`~djcrud_drf.ModelViewSet`.

Bearer security scheme
----------------------

Use :func:`~djcrud_drf.spectacular_settings` in ``settings.py`` so generated
clients know how to authenticate:

.. code-block:: python

   import djcrud_drf

   SPECTACULAR_SETTINGS = djcrud_drf.spectacular_settings(
       TITLE="My API",
   )

Bearer tokens from :doc:`../djcrud_api/index` work on DRF routes. See
:doc:`../../tutorial/frontend` for the full install walkthrough,
SPA shell, and client codegen.