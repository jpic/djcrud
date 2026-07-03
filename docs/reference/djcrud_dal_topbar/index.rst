djcrud_dal_topbar
~~~~~~~~~~~~~~~~~

.. automodule:: djcrud_dal_topbar.views
   :members:
   :show-inheritance:

.. automodule:: djcrud_dal_topbar.lookup
   :members:
   :show-inheritance:

Site search
-----------

:class:`~djcrud_dal_topbar.views.SearchView` renders paginated results at
``/search/``. :class:`~djcrud_dal_topbar.views.SiteSearchView` serves
autocomplete fragments at ``/search/autocomplete/``.

Opt models into site search with :func:`~djcrud.add_search` in ``djcrud.py``
(beside :func:`~djcrud.add_perm`). Row visibility reuses existing ``view``
queryset scoping from :func:`~djcrud.add_queryset`. The navbar partial is
:file:`djcrud_dal_topbar/templates/djcrud/_site_search.html`.