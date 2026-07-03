Tutorial
~~~~~~~~

This tutorial builds a djcrud application from the ground up. Each chapter is a
Django app in ``djcrud_example``; source files are included literally and
validated by ``pytest -m tutorial``.

* **routing** — default HTML CRUD (``routing_example``)
* **views** — custom HTML views, object actions, list actions (``views_example``)
* **permission** — row and action rules (``security_example``)
* **drf** — DRF API and OpenAPI (``drf_example``)
* **spa** — SPA shell and client codegen (``spa_example``)
* **agents** — MCP tools over the DRF API (``drf_example/djcrud.py``)

Optional packages (``djcrud_history``, ``djcrud_debug``, …) are covered in
:doc:`../install` — they work as soon as you add them to ``INSTALLED_APPS``.

.. toctree::
   :maxdepth: 1
   :caption: Chapters:

   routing
   views
   permission
   drf
   spa
   agents