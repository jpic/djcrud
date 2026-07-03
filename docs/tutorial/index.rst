Tutorial
~~~~~~~~

This tutorial builds a djcrud application from the ground up. Each chapter is a
Django app in ``djcrud_example``; source files are included literally and
validated by ``pytest -m tutorial``.

Optional packages (``djcrud_history``, ``djcrud_debug``, …) are covered in
:doc:`../install` — they work as soon as you add them to ``INSTALLED_APPS``.

.. toctree::
   :maxdepth: 1
   :caption: Chapters:

   routing
   views
   permission
   frontend
   agents
