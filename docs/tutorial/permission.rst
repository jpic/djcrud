Permissions
=============

Goal
----

Scope which rows a user can reach and which actions they may perform. Rules
registered in ``djcrud.py`` with :func:`~djcrud.add_perm` and
:func:`~djcrud.add_queryset` are **shared** across every CRUD surface:
**HTML** pages, the **API** (DRF ViewSets), and **MCP** agents that proxy
Bearer calls to ``/api/``.

The ``djcrud_example.security_example`` app demonstrates owner-based rules on
the ``Document`` model at ``/secured-document/`` in :file:`djcrud.py`. If you
are porting from djmvc controller ``get_queryset`` overrides, see
:doc:`../migrating-from-djmvc`.

Expected behavior
-----------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 20 25

   * - User
     - list/detail
     - create
     - update/delete own
     - update/delete others
   * - Anonymous
     - all rows visible
     - denied
     - denied
     - denied
   * - Authenticated
     - all rows visible
     - allowed
     - allowed
     - denied

Permission registry
-------------------

:meth:`~djcrud.Site.build` imports every ``djcrud.py`` module. Define check
and scoper functions, register rules, and append the router.

Bind one *check* to several actions with comma-separated shortcodes:

.. code-block:: python

   djcrud.add_perm(ItemRouter, "view,add,change,delete", check=djcrud.authenticated)
   djcrud.add_perm(Article, "publish", check=can_publish, router=ArticleRouter)

Full secured-document example:

.. literalinclude:: ../../src/djcrud_example/security_example/djcrud.py

* ``add_perm(..., router="secured-document")`` applies rules only to views under
  that router codename.
* Anonymous users may list and view every row (``view`` check always returns
  ``True``).
* Authenticated users may create rows; change and delete require ownership (or
  superuser).
* ``add_queryset`` narrows update and delete querysets so other users' rows
  return 404.

Try it
------

Log in as two users (see :doc:`../install`), create documents with different
owners, and visit
`http://localhost:8000/secured-document/ <http://localhost:8000/secured-document/>`_.

Each user can change and delete only their own rows; anonymous visitors can
browse list and detail.

Tests
-----

`tests/test_security_example.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_security_example.py>`_

Next: :doc:`views` customizes list views, object actions, and bulk list actions.