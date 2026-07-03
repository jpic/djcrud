ModelRouter and site
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: djcrud.ModelRouter
   :members:
   :show-inheritance:

.. autoclass:: djcrud.Site
   :members:
   :show-inheritance:

.. autoclass:: djcrud.Home
   :members:
   :show-inheritance:

.. data:: djcrud.site

   Root :class:`~djcrud.Site` instance. Before :meth:`~djcrud.Site.build`,
   ``site.routes`` is the declaration list — append routers from each app's
   ``djcrud.py`` with ``site.routes.append(...)`` (see :doc:`../tutorial/routing`).
   Call ``djcrud.site.build()`` from your project's ``urls.py`` to autodiscover
   those modules and obtain ``urlpatterns``.

   After build, inspect the URL tree with ``python manage.py show_urls`` (see
   :doc:`../tutorial/routing`).