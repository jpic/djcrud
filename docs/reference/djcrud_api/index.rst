djcrud_api
~~~~~~~~~~

Optional Bearer token authentication for API clients. This package does **not**
provide CRUD JSON endpoints — use :doc:`../djcrud_drf/index` for REST APIs.

Features
========

* **Bearer token** authentication (no session cookie, no CSRF on token requests)
* **Login** endpoint to exchange username/password for a short-lived token
* **Token management** HTML UI at ``/api/token/``

Routes
======

:mod:`djcrud_api` registers login and token routes on :data:`djcrud_drf.router`
when ``djcrud_drf`` is installed (see :doc:`../../tutorial/drf`):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - URL
     - View
   * - ``/api/login/``
     - :class:`~djcrud_api.views.ApiLoginView` — username/password → 1-hour token
   * - ``/api/token/``
     - :class:`~djcrud_api.views.TokenRouter` — manage API tokens (HTML)

Enable the package
==================

Add ``djcrud_api`` to ``INSTALLED_APPS`` and register the Bearer middleware
(**required** for token auth and CSRF exemption). Full steps are in
:doc:`../../tutorial/drf`:

.. code-block:: python

   MIDDLEWARE = [
       "django.middleware.security.SecurityMiddleware",
       "django.contrib.sessions.middleware.SessionMiddleware",
       "djcrud_api.middleware.BearerCsrfMiddleware",   # before CSRF
       "django.middleware.locale.LocaleMiddleware",
       "django.middleware.common.CommonMiddleware",
       "django.middleware.csrf.CsrfViewMiddleware",
       "django.contrib.auth.middleware.AuthenticationMiddleware",
       "djcrud_api.middleware.BearerUserMiddleware",     # after session auth
       "django.middleware.messages.middleware.MessageMiddleware",
       "django.middleware.clickjacking.XFrameOptionsMiddleware",
   ]

Run migrations after enabling the app:

.. code-block:: bash

   python manage.py migrate

Upgrading from ``djmvc_api``
============================

If the database already applied ``djmvc_api`` or ``djmvc_swagger`` migrations,
``djcrud_api`` migrations ``0002`` and ``0003`` rename the token table and
rewrite ``django_migrations`` app labels automatically. See
:ref:`api-token-upgrade` in :doc:`../../migrating-from-djmvc`.

Bearer authentication
=====================

Obtaining a token
-----------------

.. code-block:: bash

   curl -X POST http://localhost:8000/api/login/ \
     -H 'Content-Type: application/json' \
     -d '{"username": "su", "password": "su"}'

Using a token with :doc:`../djcrud_drf/index`:

.. code-block:: bash

   curl http://localhost:8000/api/product/ \
     -H 'Authorization: Bearer <token>'

API reference (modules)
=======================

.. automodule:: djcrud_api.views
   :members:
   :show-inheritance:

.. automodule:: djcrud_api.models
   :members:
   :show-inheritance:

.. automodule:: djcrud_api.middleware
   :members:
   :show-inheritance: