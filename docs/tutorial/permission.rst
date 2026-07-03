Permissions
=============

Goal
----

Scope which rows a user can reach and which actions they may perform. Rules
registered in ``djcrud.py`` with :func:`~djcrud.permissions.add_perm` are **shared** across
every CRUD surface: **HTML** pages, the **API** (DRF ViewSets), and **MCP**
agents that proxy Bearer calls to ``/api/``.

The ``djcrud_example.security_example`` app demonstrates this on a single
``Document`` model at ``/secured-document/``.

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

:meth:`~djcrud.Site.build` imports every ``djcrud.py`` module. Register rules,
then append the router:

.. literalinclude:: ../../src/djcrud_example/security_example/djcrud.py

* ``view`` — everyone (``lambda …: True``); ``add_queryset`` hides drafts from
  strangers (published rows only, unless owner or superuser).
* ``add`` — authenticated users only.
* ``change`` / ``delete`` — owner or superuser (``secured_document_change``).
* ``publish`` — owner of a draft only (``can_publish``).

Try it
------

Log in as two users (see :doc:`../install`), create documents with different
owners, and visit
`http://localhost:8000/secured-document/ <http://localhost:8000/secured-document/>`_.

For **Publish**, open a draft you own at
`http://localhost:8000/secured-document/<pk>/ <http://localhost:8000/secured-document/%3Cpk%3E/>`_.

.. figure:: /_static/screenshots/publish-action-menu.png
   :alt: Object menu with Publish action on a draft document
   :align: center
   :width: 90%

.. figure:: /_static/screenshots/publish-action-success.png
   :alt: Document detail after publishing
   :align: center
   :width: 90%

Tests
-----

* `tests/test_security_example.py <https://github.com/jpic/djcrud/blob/master/tests/test_security_example.py>`_

Next: :doc:`drf` adds an optional JSON API; :doc:`spa` adds the SPA shell and
client codegen.