Views
=====

Goal
----

Replace default views, add object actions, register bulk list actions, and opt
models into site-wide search. Four tutorial apps each ship a single ``djcrud.py``
— no extra modules:

* ``views_example`` — cloned :py:class:`~djcrud.views.list.ListView` on ``Article``
* ``action_example`` — object form action on ``Memo``
* ``listaction_example`` — bulk action on ``Post``
* ``search_example`` — :func:`~djcrud.search.add_search` opt-in on ``Page``

ListView customization
----------------------

:py:class:`~djcrud.views.list.ListView` is the view djcrud invests in by default
— search, filter, tables2, pagination, and list actions. Clone it to set table
columns, filter fields, and page size:

.. literalinclude:: ../../src/djcrud_example/views_example/djcrud.py

No ``add_perm`` here — default Django permissions apply (superuser passes).
Log in as ``su`` / ``su`` (see :doc:`routing`). Permission rules are covered in
:doc:`permission` and the ``security_example`` app.

Visit `http://localhost:8000/article/ <http://localhost:8000/article/>`_.

.. figure:: /_static/screenshots/article-list.png
   :alt: Article list with filter form and pagination
   :align: center
   :width: 90%

   Cloned list view with custom columns, filter fields, and page size.

Object action
-------------

Custom routes are not limited to CRUD. ``action_example`` appends a
**Duplicate** :py:class:`~djcrud.views.objectform.ObjectFormView` that opens a
confirmation modal from the object menu and calls ``form_valid`` — no
``add_perm`` here (default superuser access, same as the list view above):

.. literalinclude:: ../../src/djcrud_example/action_example/djcrud.py

Try it on a memo at
`http://localhost:8000/memo/<pk>/ <http://localhost:8000/memo/%3Cpk%3E/>`_.

.. figure:: /_static/screenshots/duplicate-action-menu.png
   :alt: Object menu with Duplicate action on a memo
   :align: center
   :width: 90%

   Detail object menu with a custom object action.

.. figure:: /_static/screenshots/duplicate-action-success.png
   :alt: Memo detail after duplicating
   :align: center
   :width: 90%

   After confirming, a success toast is shown.

State-based object actions gated by ``add_perm`` are covered in :doc:`permission`.

List action
-----------

Bulk actions follow the same pattern as built-in bulk delete (see :doc:`routing`).
On ``Post``, subclass :py:class:`~djcrud.views.list_action.ListActionView`, tag it
``list_action``, and append it to the router ``routes``:

.. literalinclude:: ../../src/djcrud_example/listaction_example/djcrud.py

Try it at `http://localhost:8000/post/ <http://localhost:8000/post/>`_ — create a
few posts, select rows, and click **Set category**:

.. figure:: /_static/screenshots/list-action-bar.png
   :alt: List action bar with row selection
   :align: center
   :width: 90%

   Selected rows open the floating ``<list-action-bar>`` with permitted bulk
   actions. When list actions are gated per object, only rows the user may
   act on get checkboxes, and the bar dynamically shows only the actions
   allowed for the entire current selection.

.. figure:: /_static/screenshots/set-category-modal.png
   :alt: Set category bulk action modal
   :align: center
   :width: 90%

   Custom :py:class:`SetCategoryView` — same pattern as the built-in bulk
   delete shown in :doc:`routing`.

Site search
-----------

With ``djcrud_dal_topbar`` installed (see :ref:`install-site-search`), opt a model
into navbar search and the results page at ``/search/?q=…``. ``search_example``
registers its own ``Page`` model:

.. literalinclude:: ../../src/djcrud_example/search_example/djcrud.py

Try it at `http://localhost:8000/page/ <http://localhost:8000/page/>`_ after
creating a few pages, then search from the navbar.

Mixin survey
------------

djcrud builds each generic view from **mixins** — small classes that add one
concern (filtering, pagination, tables, forms, …). Override mixin
**attributes** on a cloned view or subclass; templates read them from the
``view`` object in context.

See :doc:`../reference/mixins/index` for every mixin and overridable attribute. Generic
views that combine them are listed under :doc:`../reference/views/index`.

For screenshots of list, filter, pagination, object-menu, and list-action mixins
in action, see the sections above.

List display
    :py:class:`~djcrud.views.list.ListMixin` —
    :attr:`~djcrud.views.list.ListMixin.default_template_name`,
    :attr:`~djcrud.views.list.ListMixin.tags`,
    :attr:`~djcrud.views.list.ListMixin.permission_shortcode`,
    :attr:`~djcrud.views.list.ListMixin.empty_list_message`

    :py:class:`~djcrud.views.search.SearchMixin` —
    :attr:`~djcrud.views.search.SearchMixin.search_param`,
    :attr:`~djcrud.views.search.SearchMixin.search_fields`

    :py:class:`~djcrud.views.filter.FilterMixin` —
    :attr:`~djcrud.views.filter.FilterMixin.filter_fields`,
    :attr:`~djcrud.views.filter.FilterMixin.filter_form_class`,
    :attr:`~djcrud.views.filter.FilterMixin.filter_target`

    :py:class:`~djcrud.views.pagination.PaginationMixin` —
    :attr:`~djcrud.views.pagination.PaginationMixin.paginate_by`,
    :attr:`~djcrud.views.pagination.PaginationMixin.per_page_options`,
    :attr:`~djcrud.views.pagination.PaginationMixin.page_kwarg`,
    :attr:`~djcrud.views.pagination.PaginationMixin.per_page_kwarg`,
    :attr:`~djcrud.views.pagination.PaginationMixin.pagination_target`

    :py:class:`~djcrud.views.tables2.Tables2Mixin` —
    :attr:`~djcrud.views.tables2.Tables2Mixin.table_template`,
    :attr:`~djcrud.views.tables2.Tables2Mixin.table_fields`

Forms and objects
    :py:class:`~djcrud.views.form.FormMixin` —
    :attr:`~djcrud.views.form.FormMixin.default_template_name`,
    :attr:`~djcrud.views.form.FormMixin.form_attributes`

    :py:class:`~djcrud.views.object.ObjectMixin` — object detail URLs and
    breadcrumbs (see :doc:`../reference/mixins/object`)

    :py:class:`~djcrud.views.modelform.ModelFormMixin` — model forms for
    create/update

    :py:class:`~djcrud.views.delete.DeleteMixin` —
    :attr:`~djcrud.views.delete.DeleteMixin.default_template_name`,
    :attr:`~djcrud.views.delete.DeleteMixin.icon`,
    :attr:`~djcrud.views.delete.DeleteMixin.color`

List actions and permissions
    :py:class:`~djcrud.views.list_action.ListActionMixin` — bulk actions from the
    list action bar (see **List action** above). Per-row permissions are
    reflected both in checkbox visibility (``CheckboxColumn``) and in the
    dynamic filtering of buttons inside ``<list-action-bar>`` via
    ``data-list-actions`` / ``data-codename`` attributes.

    :py:class:`~djcrud.views.action.ActionMixin` — per-object permission checks
    on delete/update and custom object actions

    :py:class:`~djcrud.view.ViewMixin` —
    :attr:`~djcrud.view.ViewMixin.permission_shortcode`

Templates and model binding
    :py:class:`~djcrud.views.template.TemplateViewMixin` —
    :attr:`~djcrud.views.template.TemplateMixin.default_template_name` via
    ``default_template_name`` on concrete views

    :py:class:`~djcrud.model.ModelMixin` — resolves ``model`` from the enclosing
    :py:class:`~djcrud.ModelRouter`

    :py:class:`~djcrud.views.log.LogMixin` — audit logging when
    ``djcrud_history`` is installed

Further topics
    Optional packages (history, debug, auth) are described in :doc:`../install`.

    Menus and tags — tag views with ``navigation``, ``object``, or
    ``list_action``. Use ``router.get_tagged_views('object', request=request,
    object=obj)`` in templates.

    Runtime route changes — after ``site.build()``, swap or remove routes on the
    live registry (``site.routes['list'] = …``, ``del site.routes['delete']``).

    Routing debug — add ``djcrud_debug`` and browse
    `http://localhost:8000/debug/router/ <http://localhost:8000/debug/router/>`_ as
    superuser.

Tests
-----

* `tests/test_views_example.py <https://github.com/jpic/djcrud/blob/master/tests/test_views_example.py>`_
* `tests/test_action_example.py <https://github.com/jpic/djcrud/blob/master/tests/test_action_example.py>`_
* `tests/test_listaction_example.py <https://github.com/jpic/djcrud/blob/master/tests/test_listaction_example.py>`_
* `tests/test_search_example.py <https://github.com/jpic/djcrud/blob/master/tests/test_search_example.py>`_

Next: :doc:`drf` adds an optional JSON API; :doc:`spa` adds the SPA shell and
client codegen.
