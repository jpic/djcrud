Views
=====

Goal
----

Replace default views, add object actions, and register bulk list actions.
``djcrud_example.views_example`` splits each concern into a submodule; ``djcrud.py``
imports and registers them on :data:`djcrud.site`.

Registration
------------

.. literalinclude:: ../../src/djcrud_example/views_example/djcrud.py

State-based object action
-------------------------

Custom routes are not limited to CRUD. :file:`example_action.py` adds a **Publish**
object action on ``Article`` (gated by a ``publish`` rule in ``djcrud.py`` — owner
+ draft only; see :doc:`permission`, :doc:`drf` for the API surface, and
:doc:`agents` for MCP):

.. literalinclude:: ../../src/djcrud_example/views_example/example_action.py

Try it on a draft article at
`http://localhost:8000/article/<pk>/ <http://localhost:8000/article/%3Cpk%3E/>`_.

.. figure:: /_static/screenshots/publish-action-menu.png
   :alt: Object menu with Publish action on a draft article
   :align: center
   :width: 90%

   Detail object menu — **Publish** is visible only while the article is a draft.

.. figure:: /_static/screenshots/publish-action-success.png
   :alt: Article detail after publishing
   :align: center
   :width: 90%

   After publishing, the action disappears and the row shows as published.

List action
-----------

Bulk actions follow the same pattern as built-in bulk delete (see :doc:`routing`).
On ``Post``, subclass :py:class:`~djcrud.views.list_action.ListActionView`, tag it
``list_action``, and append it to the router ``routes``:

.. literalinclude:: ../../src/djcrud_example/views_example/example_listaction.py

Try it at `http://localhost:8000/post/ <http://localhost:8000/post/>`_ — create a
few posts, select rows, and click **Set category**:

.. figure:: /_static/screenshots/list-action-bar.png
   :alt: List action bar with row selection
   :align: center
   :width: 90%

   Selected rows open the floating ``<list-action-bar>`` with permitted bulk
   actions.

.. figure:: /_static/screenshots/set-category-modal.png
   :alt: Set category bulk action modal
   :align: center
   :width: 90%

   Custom :py:class:`SetCategoryView` — same pattern as the built-in bulk
   delete shown in :doc:`routing`.

ListView customization
----------------------

:py:class:`~djcrud.views.list.ListView` is the view djcrud invests in by default
— search, filter, tables2, pagination, and list actions. Clone it to set table
columns, filter fields, and page size. Add a second update route for a single
field in the object menu:

.. literalinclude:: ../../src/djcrud_example/views_example/example_listview.py

Visit `http://localhost:8000/article/ <http://localhost:8000/article/>`_.

.. figure:: /_static/screenshots/article-list.png
   :alt: Article list with filter form and pagination
   :align: center
   :width: 90%

   Cloned list view with custom columns, filter fields, and page size.

Open an article's detail page — the object menu shows both **Change Article**
and **Change category**:

.. figure:: /_static/screenshots/article-detail.png
   :alt: Article detail with object action menu
   :align: center
   :width: 90%

   Default update plus :py:class:`CategoryUpdateView` in the object menu.

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
    :attr:`~djcrud.views.search.SearchMixin.search_fields`,
    :attr:`~djcrud.views.search.SearchMixin.site_search`

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
    list action bar (see **List action** above)

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

    Internationalization — djcrud ships French translations; wrap user-visible
    strings in ``gettext`` when overriding views (see ``example_listaction.py``).

Tests
-----

`tests/test_views_example.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_views_example.py>`_

Next: :doc:`drf` adds an optional JSON API; :doc:`spa` adds the SPA shell and
client codegen.
