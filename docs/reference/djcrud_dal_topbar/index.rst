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

:class:`~djcrud_dal_topbar.views.SiteSearchView` is registered on :data:`djcrud.site` at
``/search/``. Discovery helpers in :mod:`djcrud_dal_topbar.lookup` walk model
routers and yield list views the user may search when
:attr:`~djcrud.views.search.SearchMixin.site_search` is ``True``. The navbar
partial is :file:`djcrud_dal_topbar/templates/djcrud/_site_search.html`.