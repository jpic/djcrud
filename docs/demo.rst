Try the demo
~~~~~~~~~~~~

The djcrud repository includes a complete example project with all features enabled.
This is the fastest way to explore djcrud's capabilities.

Clone and install
=================

.. code-block:: bash

   git clone https://github.com/jpic/djcrud.git
   cd djcrud
   pip install --pre -e ".[dev,docs]"

This installs djcrud in development mode with all dependencies. The ``--pre`` flag
is required for pre-release dependency versions.

Run the example project
=======================

The example project lives in ``src/djcrud_example/`` and includes:

* All djcrud apps (auth, DAL, history, debug)
* Tutorial example apps (routing, permission, views, drf, spa)
* Seeded test data with a superuser account

Initialize the database:

.. code-block:: bash

   python manage.py migrate

Start the development server:

.. code-block:: bash

   python manage.py runserver

Log in
======

Visit http://localhost:8000/auth/login/ and log in with the pre-seeded superuser:

* **Username:** ``su``
* **Password:** ``su``

Once logged in, you'll see the Bulma UI with sidebar navigation.

Explore the demo
================

**Model routers** — Visit http://localhost:8000/item/ to see a default CRUD interface
with list, create, detail, update, and delete views.

**Site search** — Use the search bar in the top navigation to search across all
models (requires ``djcrud_dal_topbar``).

**JSON API** — Enable the DRF tutorial apps in ``settings.py`` and ``urls.py``
(see :doc:`tutorial/drf`), then visit http://localhost:8000/api/docs/ for the
Swagger UI.

**Tutorial examples** — The example project includes all tutorial chapters:

* :doc:`tutorial/routing` — ``/item/`` — basic model router
* :doc:`tutorial/permission` — ``/secured-document/`` — permissions registry
* :doc:`tutorial/views` — ``/article/``, ``/post/`` — view customization and actions
* :doc:`tutorial/drf` — ``/api/product/`` and OpenAPI
* :doc:`tutorial/spa` — ``/spa/`` and client codegen

**Debug tools** — Visit http://localhost:8000/debug/router/ (superuser only)
to introspect the routing tree.

**History/Audit logging** — Visit http://localhost:8000/logentry/ to browse the
global audit log (requires ``djcrud_history``).

Next steps
==========

After exploring the demo:

1. Read the :doc:`tutorial/index` to understand how the example apps were built
2. Follow the :doc:`install` guide to create your own project
3. Review the :doc:`reference/index` for detailed API documentation

For development contributions, see :doc:`contributing`.