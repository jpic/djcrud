Install djcrud
~~~~~~~~~~~~~~

Install the package
===================

.. code-block:: bash

   pip install --pre djcrud

This installs djcrud with all runtime dependencies including the Bulma UI framework.

Upgrading from djmvc
--------------------

If your project uses the last **djmvc** release (``Controller``,
``ModelController``, ``djmvc.py``), see :doc:`migrating-from-djmvc` for the
full breaking-change guide and checklist.

.. note::

   The ``--pre`` flag is required to install pre-release versions of dependencies
   (currently ``django-autocomplete-light>=5.1``).

.. tip::

   Want to try djcrud first? See :doc:`demo` for a quick walkthrough of the example project.

For local development (tests, docs, example project):

.. code-block:: bash

   git clone https://github.com/jpic/djcrud.git
   cd djcrud
   pip install --pre -e ".[dev,docs]"

Create a Django project
========================

.. code-block:: bash

   django-admin startproject myproject
   cd myproject

Configure settings
==================

Import the djcrud apps and add Django's contrib apps:

.. code-block:: python

   # myproject/settings.py
   import djcrud.settings

   INSTALLED_APPS = djcrud.settings.INSTALLED_APPS + [
       "django.contrib.admin",
       "django.contrib.auth",
       "django.contrib.contenttypes",
       "django.contrib.sessions",
       "django.contrib.messages",
       "django.contrib.staticfiles",
       # your apps with a djcrud.py module:
       # "myapp",
   ]

:mod:`djcrud.settings.INSTALLED_APPS` includes djcrud core, Bulma UI, authentication,
autocomplete (DAL), site search, and audit logging. It does **not** include
``djcrud_api`` (Bearer tokens), ``djcrud_drf`` (REST API), or ``djcrud_mcp``
(agent MCP bridge) — enable API packages in :doc:`tutorial/frontend` and the
MCP client in :doc:`tutorial/agents` when you need them. The order ensures
``dal`` and ``dal_alight`` load before ``django.contrib.admin``.

Optional extras
===============

.. list-table::
   :header-rows: 1
   :widths: 20 35 45

   * - Extra
     - Install
     - Purpose
   * - ``drf``
     - ``pip install --pre "djcrud[drf]"``
     - DRF ViewSets, OpenAPI schema at ``/api/schema/``
   * - ``mcp``
     - ``pip install --pre "djcrud[mcp]"``
     - stdio MCP bridge (``djcrud-mcp``); requires ``[drf]`` on the Django host
   * - ``dev``
     - ``pip install --pre "djcrud[dev]"``
     - pytest, tox, splinter
   * - ``docs``
     - ``pip install --pre "djcrud[docs]"``
     - Sphinx build

Initialize the database
=======================

.. code-block:: bash

   python manage.py migrate
   python manage.py createsuperuser

Configure URLs
==============

Wire the djcrud site in your project's ``urls.py``:

.. code-block:: python

   # myproject/urls.py
   from django.contrib import admin
   from django.urls import path
   import djcrud

   urlpatterns = djcrud.site.build().urlpatterns + [
       path("admin/", admin.site.urls),
   ]

:py:meth:`~djcrud.Site.build` autodiscovers every installed app's ``djcrud.py``
module and builds the routing tree.

Start developing
================

.. code-block:: bash

   python manage.py runserver

Visit http://localhost:8000/auth/login/ to log in with your superuser credentials.

.. _install-site-search:

Enable site search
==================

``djcrud_dal_topbar`` is included in ``djcrud.settings.INSTALLED_APPS`` and
provides a site-wide autocomplete search in the navbar. No additional
installation steps are required when using :mod:`djcrud.settings`.

Next steps
==========

**Tutorial**: Start with :doc:`tutorial/routing` to create your first model router.

**Reference documentation**:

* :doc:`tutorial/frontend` — optional DRF REST API, SPA shell, and client codegen
* :doc:`tutorial/agents` — stdio MCP tools from the OpenAPI schema
* :doc:`reference/djcrud_mcp/index` — MCP bridge reference
* :doc:`reference/djcrud_dal/index` — Autocomplete for relation fields
* :doc:`reference/djcrud_dal_topbar/index` — Site-wide search in the navbar
* :doc:`reference/djcrud_history/index` — Audit logging and history views
* :doc:`reference/djcrud_auth/index` — Authentication views
* :doc:`reference/djcrud_debug/index` — Route introspection (development only)

**Example project**: See the full example project settings at `djcrud_example/settings.py on GitHub <https://github.com/jpic/djcrud/blob/master/src/djcrud_example/settings.py>`_.