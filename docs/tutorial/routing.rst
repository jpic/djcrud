Routing
=======

Goal
----

Add a Django model and expose default CRUD routes with a
:py:class:`~djcrud.ModelRouter` in ``djcrud.py``.

This chapter uses ``djcrud_example.routing_example``. It covers routing only —
no :doc:`permission`, no DRF, no Bearer tokens.

Moving pieces
-------------

djcrud builds a URL tree from a few composable types (see :doc:`../reference/index`):

**Router** (:py:class:`~djcrud.Router`, :py:class:`~djcrud.ModelRouter`)
    URL prefix (``urlpath``), sidebar ``icon``/``color``, and a ``routes`` list.
    A :py:class:`~djcrud.ModelRouter` binds a Django model and registers default
    list, create, detail, update, delete, and bulk-delete views.

**Route** (:py:class:`~djcrud.Route`)
    One URL pattern inside a router — ``urlpath``, ``urlname``, and ``codename``.
    Routes with the same codename replace each other (see below).

**View** (:py:class:`~djcrud.View`)
    Permission shortcode, template API (``view.title``, breadcrumbs), and
    Unpoly targets. Generic views combine small mixins; see :doc:`views`.

**Model**
    ``ModelRouter.model`` and :py:class:`~djcrud.model.ModelMixin` on views resolve
    the active model from the enclosing router.

.. note::

   To nest model routers under an app prefix (for example ``/inventory/item/``),
   wrap them in a :py:class:`~djcrud.Router` — the same pattern as
   ``djcrud_auth``. See :doc:`../reference/router`.

Router and registration
-----------------------

Create ``yourapp/djcrud.py``, add ``yourapp`` to ``INSTALLED_APPS``, define your
router, and append it to :data:`djcrud.site`:

.. literalinclude:: ../../src/djcrud_example/routing_example/djcrud.py

Before :py:meth:`~djcrud.Site.build`, ``site.routes`` is the declaration list;
``append()`` adds your router there. Build then autodiscovers every
``djcrud.py`` module (importing it runs the append) and gives you list, create,
detail, update, delete, and bulk-delete views with Bulma templates.

List and detail use Django's ``view`` permission (``view_item``). Create,
update, and delete use ``add``, ``change``, and ``delete``.

Override a default view
-----------------------

``ModelRouter.routes + [...]`` starts from the default route list and registers
your entries afterward. Routes with the same codename replace the default — here
the cloned :py:class:`~djcrud.views.list.ListView` overrides ``list``:

With ``djcrud_dal_topbar`` installed (see :ref:`install-site-search`), the navbar
includes a site-wide search autocomplete and results page. Models are **not**
included by default — register them in ``djcrud.py`` with
:func:`~djcrud.search.add_search`. Search uses each list's
:attr:`~djcrud.views.search.SearchMixin.search_fields` (CharField and
TextField columns by default).

.. code-block:: python

    djcrud.search.add_search(Item)

See ``search_example`` in the example project for a runnable opt-in on the
``Page`` model (``docs/tutorial/views.rst``).

Inspect routes
--------------

After ``migrate``, list every URL pattern:

.. code-block:: bash

   python manage.py show_urls

Filter by name or path:

.. code-block:: bash

   python manage.py show_urls --named-only
   python manage.py show_urls --search item

Try it
------

Log in (see :doc:`../install`) and visit
`http://localhost:8000/item/ <http://localhost:8000/item/>`_. URL names look like
``site:item:list``, ``site:item:create``.

.. figure:: /_static/screenshots/item-list.png
   :alt: Default item list with sidebar navigation
   :align: center
   :width: 90%

   Default list view for the ``Item`` model — table, sidebar navigation, and
   create action.

.. figure:: /_static/screenshots/success-toast.png
   :alt: Success toast after creating an item
   :align: center
   :width: 90%

   A success toast appears after creating a row.

With ``djcrud_history`` in ``INSTALLED_APPS`` (see :doc:`../install`), every
``ModelRouter`` also gets a history view at
`http://localhost:8000/item/<pk>/history/ <http://localhost:8000/item/%3Cpk%3E/history/>`_ with no extra code in your
``djcrud.py``.

Select rows on the list to open the built-in bulk-delete action:

.. figure:: /_static/screenshots/bulk-delete-modal.png
   :alt: Bulk delete confirmation modal
   :align: center
   :width: 90%

   Built-in :py:class:`~djcrud.views.delete.DeleteObjectsView` — registered on
   every :py:class:`~djcrud.ModelRouter` with no extra code.

Tests
-----

`tests/test_routing_example.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_routing_example.py>`_

Next: :doc:`permission` scopes querysets and permissions for multi-user apps.