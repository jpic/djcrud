Migrating from djmvc
====================

The last **djmvc** release used ``Controller``, ``ModelController``, per-app
``djmvc.py`` modules, and JSON on the same URLs as HTML. **djcrud** renames the
package and core types, moves JSON to DRF at ``/api/``, and centralizes
permissions in a registry shared by HTML, API, and MCP.

This guide is for projects already on djmvc (including
`Tildette <https://github.com/jpic/tildette>`_). Greenfield setup is in
:doc:`install` and :doc:`tutorial/index`.

Overview
--------

What changed at a glance:

.. list-table::
   :header-rows: 1
   :widths: 28 32 40

   * - Area
     - djmvc (last release)
     - djcrud
   * - Package / import
     - ``djmvc``
     - ``djcrud``
   * - Route group
     - :class:`djmvc.Controller`
     - :class:`~djcrud.Router`
   * - Model CRUD group
     - :class:`djmvc.ModelController`
     - :class:`~djcrud.ModelRouter`
   * - App hook file
     - ``myapp/djmvc.py``
     - ``myapp/djcrud.py``
   * - Row scoping
     - ``ModelController.get_queryset(self, view)``
     - :func:`~djcrud.add_queryset`
   * - Action / object gates
     - ``has_permission_object()``, ``has_permission_backend()``
     - :func:`~djcrud.add_perm`
   * - JSON CRUD
     - Same URL as HTML (``wants_json``, ``json_*``, ``get_swagger_*``)
     - DRF :class:`~djcrud_drf.ModelViewSet` at ``/api/<model>/``
   * - OpenAPI
     - Swagger 2 from view methods
     - OpenAPI 3 from drf-spectacular at ``GET /api/schema/``
   * - Bearer tokens
     - ``djmvc_api``
     - ``djcrud_api``
   * - Templates
     - ``{% load djmvc %}``
     - ``{% load djcrud %}``
   * - MCP / agents
     - ``djcrud-cli`` (formerly ``djmvc-cli``), ``DJMVC_*`` env aliases
     - ``djcrud-mcp``, ``DJCRUD_*`` env, ViewSet-based tools (see :doc:`tutorial/agents`)

There is **no** compatibility shim — plan a focused port rather than mixing
imports.

Upgrade checklist
-----------------

Work through these phases in order. Commit after each phase so regressions are
easy to bisect.

Phase A — dependencies
~~~~~~~~~~~~~~~~~~~~~~

1. Replace the package::

      pip uninstall djmvc
      pip install --pre "djcrud[drf]"

   Add ``[mcp]`` when you need the stdio MCP client (:doc:`tutorial/agents`).

2. Update ``INSTALLED_APPS`` — swap every ``djmvc_*`` app for its ``djcrud_*``
   counterpart:

   .. list-table::
      :header-rows: 1
      :widths: 40 60

      * - djmvc
        - djcrud
      * - ``djmvc``
        - ``djcrud``
      * - ``djmvc_bulma``
        - ``djcrud_bulma``
      * - ``djmvc_auth``
        - ``djcrud_auth``
      * - ``djmvc_dal``
        - ``djcrud_dal``
      * - ``djmvc_dal_topbar``
        - ``djcrud_dal_topbar``
      * - ``djmvc_history``
        - ``djcrud_history``
      * - ``djmvc_triggers``
        - ``djcrud_triggers``
      * - ``djmvc_api``
        - ``djcrud_api``
      * - *(none)*
        - ``djcrud_drf`` (new — enable for REST API)

3. Replace ``import djmvc.settings`` with ``import djcrud.settings`` in
   ``settings.py``.

4. Merge API URLs in ``urls.py`` when enabling DRF::

      import djcrud
      import djcrud_drf

      urlpatterns = (
          djcrud.site.build().urlpatterns
          + djcrud_drf.site.build().urlpatterns
      )

5. Run migrations — see :ref:`api-token-upgrade` below.

Phase B — rename surface (mechanical)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Rename each ``djmvc.py`` → ``djcrud.py``.
2. Global replace in Python:

   - ``import djmvc`` → ``import djcrud``
   - ``djmvc.Controller`` → ``djcrud.Router``
   - ``djmvc.ModelController`` → ``djcrud.ModelRouter``
   - ``djmvc.generic`` → ``djcrud.generic``
   - ``djmvc.site`` → ``djcrud.site``
   - ``from djmvc.`` → ``from djcrud.``

3. Rename classes: ``FooController`` → ``FooRouter``,
   ``FooSectionController`` → ``FooSectionRouter``. **Keep explicit**
   ``codename`` overrides unchanged — they control URL prefixes and reverse
   names, not the class suffix.

4. Templates: ``{% load djmvc %}`` → ``{% load djcrud %}``.

5. Custom CSS/JS: update selectors from ``djmvc-*`` to ``djcrud-*`` where you
   target the framework shell (e.g. immersive layout classes).

6. Tests: rebuild the site registry the same way as before, using
   ``djcrud.site``::

      import djcrud
      djcrud.site.registry.clear()
      djcrud.site.build()

Phase C — permissions registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the largest **behavioral** change. djmvc scoped rows and gated actions
on **controller and view methods**. djcrud registers rules once in ``djcrud.py``
and shares them across HTML, DRF, and MCP.

Registry API
^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - djmvc pattern
     - djcrud replacement
   * - ``ModelController.get_queryset(self, view)``
     - :func:`~djcrud.add_queryset(model, scoper=..., router=...)`
   * - ``has_permission_object()`` on action views
     - :func:`~djcrud.add_perm(model, "<shortcode>", check=..., router=...)`
   * - ``has_permission_backend()`` on a view
     - :func:`~djcrud.add_perm` with router scope or full perm string
   * - ``ModelController.has_permission(self, view)``
     - :func:`~djcrud.add_perm` on the router

Predicates compose with :func:`~djcrud.any_of`, :func:`~djcrud.all_of`,
:func:`~djcrud.authenticated`, :func:`~djcrud.superuser`, and
:func:`~djcrud.is_owner`.

Example — owner-scoped queryset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**djmvc:**

.. code-block:: python

   class FileController(djmvc.ModelController):
       model = File

       def get_queryset(self, view):
           qs = super().get_queryset(view)
           if view.request.user.is_staff:
               return qs
           return qs.filter(owner=view.request.user)

**djcrud:**

.. code-block:: python

   def file_queryset(user, *, model, action, perm, obj, router, **ctx):
       qs = model._default_manager.all()
       if user.is_staff:
           return qs
       if not user.is_authenticated:
           return qs.none()
       return qs.filter(owner=user)

   class FileRouter(djcrud.ModelRouter):
       model = File

   djcrud.add_queryset(File, scoper=file_queryset, router=FileRouter)
   djcrud.add_perm(FileRouter, "view,add,change,delete", check=djcrud.authenticated)

Full worked example: ``djcrud_example.security_example`` in
:file:`src/djcrud_example/security_example/djcrud.py` and :doc:`tutorial/permission`.

Example — custom object action
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**djmvc** — permission on the view:

.. code-block:: python

   class PublishView(ObjectMixin, ActionMixin, ModelMixin, djmvc.View):
       permission_shortcode = "publish"

       def has_permission_object(self):
           return (
               self.object.owner_id == self.request.user.pk
               and not self.object.published
           )

**djcrud** — same view class (HTML unchanged), rule in the registry:

.. code-block:: python

   def can_publish(user, *, obj, **ctx):
       if not user.is_authenticated:
           return False
       if obj is not None and (
           not djcrud.is_owner(user, obj=obj, **ctx) or obj.published
       ):
           return False
       return True

   djcrud.add_perm(Article, "publish", check=can_publish, router=ArticleRouter)

The custom action's ``permission_shortcode`` (or DRF ``@action`` method name)
must match the shortcode passed to :func:`~djcrud.add_perm`.

Router-scoped rules
^^^^^^^^^^^^^^^^^^^

When two routers share a model (as in the security example), pass
``router=MyRouter`` or ``router="secured-document"`` (the router
:attr:`~djcrud.route.Route.codename`) so rules apply only under that URL tree.

Phase D — API and agents
~~~~~~~~~~~~~~~~~~~~~~~~

djmvc served JSON from the **same paths** as HTML when the client sent
``Accept: application/json`` or used ``PUT``/``PATCH``/``DELETE``. djcrud
removes ``wants_json``, ``json_get``/``json_post``, ``get_swagger_*``, and
``ModelController.serialize()`` from HTML views. Machine clients use DRF
instead.

Per model
^^^^^^^^^

1. Add a ViewSet::

      import djcrud_drf

      class TaskViewSet(djcrud_drf.ModelViewSet):
          model = Task

2. Register it::

      djcrud_drf.site.register(TaskViewSet)

3. Register permissions in ``djcrud.py`` (same rules as HTML).

4. Remove dead JSON handlers from HTML views (``get_json_form_kwargs``,
   ``json_form_valid_response``, ``get_swagger_post``, etc.) once the ViewSet
   covers the workflow.

Custom actions
^^^^^^^^^^^^^^

Use DRF ``@action``. The method name becomes the permission shortcode and the
MCP tool suffix (``article_publish`` → ``publish`` rule):

.. code-block:: python

   from rest_framework.decorators import action
   from rest_framework.response import Response

   class ArticleViewSet(djcrud_drf.ModelViewSet):
       model = Article

       @action(detail=True, methods=["post"])
       def publish(self, request, pk=None):
           article = self.get_object()
           article.publish()
           return Response(self.get_serializer(article).data)

   djcrud.add_perm(Article, "publish", check=can_publish)

See :doc:`tutorial/agents` for the full single-file example.

URL and tool naming breaks
^^^^^^^^^^^^^^^^^^^^^^^^^^

HTML prefixes are usually **unchanged** when you preserve ``codename`` overrides
(``TasksSectionController`` at ``/taskssection/`` → ``TasksSectionRouter`` with
the same ``codename``).

The **REST API** uses a separate prefix per registered ViewSet:
``/api/<model_name_lower>/``. Agents and MCP clients that called
``/taskssection/item/`` with Bearer must switch to ``/api/task/`` (example).

MCP tool names change from path-derived heuristics to
``{model}_{drf_action}`` (e.g. ``task_list``, ``task_create``). Environment
variables rename to ``DJCRUD_BASE_URL`` and ``DJCRUD_TOKEN``; ``DJMVC_*`` and
``TILDETTE_*`` remain accepted aliases (:doc:`reference/djcrud_mcp/index`).

.. _api-token-upgrade:

Database upgrade (``djmvc_api`` → ``djcrud_api``)
-------------------------------------------------

Enabling ``djcrud_api`` runs migrations that upgrade existing databases:

* ``0002_rename_from_djmvc_swagger`` — renames ``djmvc_swagger_token`` →
  ``djmvc_api_token`` if present.
* ``0003_rename_from_djmvc_api`` — renames ``djmvc_api_token`` →
  ``djcrud_api_token`` and updates ``django_migrations`` rows from
  ``djmvc_api`` to ``djcrud_api``.

After ``pip install djcrud`` and updating ``INSTALLED_APPS``::

   python manage.py migrate

Existing Bearer tokens remain valid (same table, new name). No manual SQL is
required for standard upgrades.

Patterns that stay the same
---------------------------

These conventions carry over with import renames only:

* ``djcrud.site.routes.append(MyRouter)`` — same as ``djmvc.site.routes.append``
* ``ModelRouter.routes + [MyView.clone(...)]`` — extend or replace by codename
* View metadata — ``icon``, ``color``, ``title``, ``tags``, ``table_fields``,
  ``fields``, ``search_fields``, ``paginate_by``
* ``ObjectMixin``, ``ActionMixin``, ``ModelMixin``, ``FormMixin``
* ``Clonable.clone()`` for ad-hoc view variants
* Reverse names — ``site:<section>:<router>:<view>`` (replace ``controller`` in
  docs and tests with ``router``; the namespace string is unchanged if
  ``codename`` values are unchanged)
* ``FULL_PAGE_LINK_ATTRIBUTES`` — still on ``djcrud.redirect``

What to remove
--------------

After the port, delete or stop relying on:

* ``wants_json`` branching and ``json_*`` methods on HTML views
* ``get_swagger_get`` / ``get_swagger_post`` on views
* ``ModelController.json_fields``, ``serialize()``, ``get_<field>_json()``
* Controller-level ``get_queryset`` / ``has_permission`` overrides (moved to
  registry)
* ``djmvc-cli`` entry point — renamed to ``djcrud-cli``; standalone MCP uses ``djcrud-mcp``
  extra
* ``TILDETTE_CONTROLLER_PREFIX`` / path-prefix OpenAPI filtering — replace with
  ViewSet registration (:doc:`design/djcrud_mcp`)

Large-app porting notes (Tildette)
----------------------------------

Tildette is the reference large port. Suggested order:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - App
     - Notes
   * - ``tildette_triggers``
     - Small; swap ``djmvc_triggers`` imports first
   * - ``tildette_mcp``
     - Registry section; non-CRUD secret endpoints become DRF ``@action`` or
       APIView routes in ``/api/schema/`` (see :doc:`design/djcrud_mcp`)
   * - ``tildette_tasks``
     - Heavy JSON on views; add ``TaskViewSet``; MCP tool names change
   * - ``tildette_workspace``
     - Multiple ``get_queryset`` overrides → per-model ``add_queryset``
   * - ``tildette_process``
     - Process scoping + shared helpers (update import paths)
   * - ``tildette_acp``
     - HTML routers; WebSocket timeline paths are **not** djcrud (unchanged)
   * - Provider apps (grok, claude, …)
     - Small ``FormView`` routers under agents section

Update Tildette docs (``docs/reference/urls-and-sections.rst``,
``docs/install.rst``) when the port lands.

Verification
------------

After each phase:

**HTML**

* Sidebar navigation shows only routes the user may access
* Object action menus respect registry checks
* Rows outside scoped querysets return 404 on detail/update/delete

**API**

* ``GET /api/schema/`` lists registered ViewSets
* Bearer CRUD returns 403 for denied actions, 404 for out-of-scope PKs
* Custom ``@action`` endpoints match registry shortcodes

**MCP / agents**

* Tools follow ``{model}_{action}`` naming
* Token env vars set (``DJCRUD_TOKEN`` or alias)
* No hardcoded ``controller_prefix`` path filters

Further reading
---------------

* :doc:`philosophy` — why the registry exists
* :doc:`tutorial/permission` — ``add_perm`` / ``add_queryset`` in depth
* :doc:`tutorial/drf` — DRF setup
* :doc:`tutorial/agents` — MCP after DRF
* :doc:`design/djcrud_mcp` — tool discovery design