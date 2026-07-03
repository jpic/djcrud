Philosophy
~~~~~~~~~~

**Faster Django development by getting more out of less.** djcrud is not a
parallel web stack — it is a thin MVC layer on top of Django that removes
repetitive wiring while keeping Django's models, permissions, and generic views.

Structure is code, not configuration
====================================

Routing is declared by **nesting routers and views**, not by hand-editing
``urls.py`` for every endpoint. A :py:class:`~djcrud.ModelRouter` on a model
gives you list, detail, create, update, delete, and bulk delete. URL segments,
names, and nesting follow from class names and conventions.

Each app appends routers to :data:`djcrud.site` in ``djcrud.py`` (``site.routes.append(...)``).
:py:meth:`~djcrud.Site.build` autodiscovers those modules — the same “drop a
module in each app” pattern as Django admin's ``admin.py``.

Sane defaults, surgical overrides
=================================

Defaults should work on day one. Customization should be **local and explicit**:

- Replace a default view by registering another route with the **same codename**
- Extend with ``ModelRouter.routes + [MyView]``
- Tweak at runtime: ``site.routes['delete'] = MyDelete.clone(...)``
- Use :py:meth:`~djcrud.clonable.Clonable.clone` to specialize without new
  module-level classes

The :doc:`registry <reference/registry>` is an ordered override table, not a
pile of magic.

The view *is* the template API
==============================

.. epigraph::

   Ain't no way I'm defining ``get_context_data`` for everything.

Add a method or property on the view → use ``{{ view.something }}`` in the
template. :py:class:`~djcrud.views.template.TemplateMixin` puts ``view`` in
context by default. Template logic stays on the view class, not scattered
across context dicts and one-off template tags.

Template power without template-tag sprawl
==========================================

.. epigraph::

   Ain't no way I'm defining a templatetag for everything.

Django templates get Jinja-like freedom via ``{% eval %}`` (see
:doc:`reference/templatetags`), plus filters like ``html_attributes`` and
``unpoly_attributes``. Call view methods from templates; render attribute dicts
without bespoke tags for every case.

One permissions framework, every surface
======================================

Permissions **always** go through djcrud's registry — not ad hoc checks in
templates, views, serializers, or future tool handlers. Register rules once in
each app's ``djcrud.py`` with :func:`~djcrud.add_perm` and
:func:`~djcrud.add_queryset`; :meth:`~djcrud.Site.build` imports them
automatically.

The same rules drive every CRUD surface you hang off the route tree:

- **HTML** — :py:meth:`~djcrud.view.ViewMixin.has_permission` before dispatch;
  menus via :py:meth:`~djcrud.router.Router.get_tagged_views`
- **API** — :doc:`reference/djcrud_drf/index` ViewSets call the same registry
  through :py:meth:`~djcrud.ModelRouter.has_permission`
- **MCP and other agents** — :doc:`reference/djcrud_mcp/index` mirrors
  registered :class:`~djcrud_drf.ModelViewSet` CRUD automatically; Bearer HTTP
  hits the same registry as HTML/API — no per-action decorators, no parallel
  auth stack (see :doc:`design/djcrud_mcp`)

Your application code lives **inside** this framework: predicates such as
:func:`~djcrud.superuser`, :func:`~djcrud.authenticated`, :func:`~djcrud.is_owner`,
:func:`~djcrud.any_of`, and :func:`~djcrud.all_of` compose the checks you
register. Override a router or view only when a route needs a one-off escape
hatch.

Secure by default: superuser or nothing
=======================================

**Secure by default** means **superuser or nothing** until you explicitly open
access. A freshly registered :py:class:`~djcrud.ModelRouter` does not grant
CRUD to regular users, anonymous visitors, or API tokens — only superusers pass
until you add rules.

Every view checks permissions **before** dispatch: anonymous users go to login;
authenticated users who fail the check get 403. Navigation, object menus, and
list-action bars call the same checks, so UI never advertises routes the user
cannot use.

Open access deliberately in ``djcrud.py``:

.. code-block:: python

   import djcrud
   from djcrud.permissions import authenticated, is_owner, superuser, any_of

   # Grant list/detail to any logged-in user on this router
   djcrud.add_perm(ItemRouter, "view", check=authenticated)

   # Writes: owner or superuser
   djcrud.add_perm(
       ItemRouter,
       "change",
       check=any_of(superuser, is_owner),
   )

   # Narrow row visibility for writes (see tutorial/permission)
   djcrud.add_queryset(Item, "change", scoper=my_change_queryset)

Model routers delegate to the registry:

- :py:meth:`~djcrud.ModelRouter.has_permission` — who may perform each action
- :py:meth:`~djcrud.ModelRouter.get_queryset` — which rows exist for that user

Lists, object views, bulk actions, and API list endpoints share those
querysets. PKs outside the scoped queryset → 404, not a leak.

See :doc:`tutorial/permission` for owner-based ``add_perm`` / ``add_queryset``
examples.

Basic template you can copy
===========================

The main goal for **code sharing** is a small, secure shell you inherit instead
of re-wiring ``urls.py``, permissions, and navigation in every project.

**Standard pages** use ``djcrud/base.html``: top navbar, sidebar built from
``navigation`` tags, and ``[up-main]`` for content. **SPA pages** subclass
:py:class:`~djcrud.views.spa.SPAView` and use ``djcrud/base_spa.html`` — same
sidebar navigation, full-screen client mount, ``unpoly_target = 'body'``.

Both shells plug into the **same permissions framework**: dispatch runs
:py:meth:`~djcrud.view.ViewMixin.has_permission` before rendering (superuser or
nothing until you register grants); navigation lists only permitted views (see
:py:meth:`~djcrud.router.Router.get_tagged_views`).

Declare assets with Django :class:`~django.forms.Media` — no inline JavaScript in
the reference templates:

.. literalinclude:: ../src/djcrud_example/spa_example/djcrud.py
   :language: python

The shell loads Bulma, Unpoly, CSRF config, and sidebar markup; your subclass
sets :attr:`~djcrud.views.spa.SPAView.mount_element` and adds the client bundle
via ``class Media``. Copy ``base.html`` or extend ``SPAView`` — routing and
security stay on the djcrud defaults.

Menus are introspected, not hardcoded
=====================================

Views carry **``tags``** (``topbar``, ``object``, ``list_action``, …).
Routers expose :py:meth:`~djcrud.router.Router.get_tagged_views`,
which instantiates each candidate, runs :py:meth:`~djcrud.view.ViewMixin.has_permission`,
and returns only what the current user (and object, if any) may see.

Navigation is **derived from the route tree**, not duplicated in every template.

.. figure:: /_static/screenshots/item-list.png
   :alt: Sidebar navigation built from tagged list views
   :align: center
   :width: 90%

   Sidebar entries come from views tagged ``navigation``; router ``icon``
   attributes render beside each label.

Composition over monoliths
==========================

Generic views are **stacks of small mixins** — one concern each (filter,
pagination, tables2, form, object, delete, list_action, …). Override mixin
**attributes** on a subclass or clone; templates read them from ``view``.

:doc:`tutorial/views` is the manifesto: understand the mixins, understand the
whole system. See :doc:`reference/mixins/index` for each mixin.

Django all the way down
=======================

djcrud embraces Django rather than fighting it:

- ``user.has_perm()`` and custom backends (crudlfap lineage)
- Django generic views and ``urlpatterns``
- Bulma templates that are **simple enough to copy and adapt** — reference UI,
  not a locked theme

Optional packages (``djcrud_auth``, ``djcrud_history``, ``djcrud_debug``) plug in
the same way: add to ``INSTALLED_APPS``, routes appear. See :doc:`install`.

The optional :doc:`reference/djcrud_drf/index` package adds a DRF layer on
``/api/`` that calls the **same** :func:`~djcrud.add_perm` registry as HTML
views — install with ``pip install djcrud[drf]`` when you need REST; widen API
access with the same ``djcrud.py`` rules, not duplicate serializer guards.

The optional :doc:`reference/djcrud_mcp/index` client (``pip install djcrud[mcp]``)
exposes tagged schema operations as stdio MCP tools for agents — install on the
subprocess host, not in ``INSTALLED_APPS``.

Progressive complexity
======================

The :doc:`tutorial/index` mirrors how you would actually adopt djcrud:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Chapter
     - Idea
   * - :doc:`tutorial/routing`
     - One model → full CRUD (superuser-only until you open it); override
       defaults by codename
   * - :doc:`tutorial/permission`
     - **Your** rules via ``add_perm`` / ``add_queryset`` — same registry for
       HTML, API, and future MCP agents
   * - :doc:`tutorial/views`
     - Clone list views, object actions, bulk list actions, mixin tour
   * - :doc:`tutorial/spa`
     - DRF API and SPA shell reusing the permissions you registered in step 2
   * - :doc:`tutorial/agents`
     - stdio MCP bridge (``djcrud_mcp``) over the same API and permissions

Each chapter is a working app in ``djcrud_example``, literal-included in the
docs, validated by ``pytest -m tutorial``. The adoption path is deliberate:
ship locked-down CRUD first, then widen access in ``djcrud.py`` without
touching templates or serializers.

In one sentence
===============

**Declare a tree of routers and views, inherit routing and superuser-only CRUD,
register your permission rules once in ``djcrud.py`` for HTML/API/MCP, expose the
view object to templates, and override only what you need — presentation through
composable mixins and introspected menus.**

That is the voice behind “Get more out of less” and the README's informal
“ain't no way I'm…” lines: less boilerplate, fewer files, same Django
underneath.
