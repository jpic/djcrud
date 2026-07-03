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

Register ViewSets in each app's ``djcrud.py`` (loaded by
:meth:`djcrud.Site.build`). Call :meth:`djcrud_drf.DrfSite.build` after
:meth:`djcrud.Site.build` in ``urls.py``. Split into other modules via imports
if you prefer — HTML :class:`~djcrud.ModelRouter` registration in the same file
is optional and independent.

.. code-block:: python

   # myapp/djcrud.py
   import djcrud
   import djcrud_drf
   from .models import Item

   class ItemRouter(djcrud.ModelRouter):
       model = Item

   djcrud.site.routes.append(ItemRouter)

   class ItemViewSet(djcrud_drf.ModelViewSet):
       model = Item

   djcrud_drf.site.register(ItemViewSet)

Audit logging
=============

:class:`~djcrud_drf.ModelViewSet` mixes in :class:`~djcrud_drf.LogMixin`, which
writes Django admin ``LogEntry`` rows on create, update, and destroy (same
envelope format as :class:`~djcrud.views.log.LogMixin` on HTML views). When
``djcrud_history`` is installed, API mutations appear on each model's history
view automatically.

Set ``log_actions = False`` on a ViewSet subclass to disable logging, or pass a
``frozenset`` of action names (``"update"`` covers ``partial_update``).

Permissions
===========

:func:`~djcrud.permissions.add_perm` and :func:`~djcrud.permissions.add_queryset` registered in each
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
:doc:`../../tutorial/drf` for the install walkthrough and
:doc:`../../tutorial/spa` for the SPA shell and client codegen.