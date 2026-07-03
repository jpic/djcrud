SPA shell
=========

Embed a client framework (Svelte in this example) inside djcrud's navigation
shell while keeping sidebar navigation server-rendered in HTML. Example app:
``spa_example`` (``/spa/``).

Complete :doc:`drf` first if you want the demo to call ``/api/product/`` from
the browser. The SPA chapter itself only needs ``djcrud.site`` — no ViewSet
registration required.

SPA template convention
-----------------------

:py:class:`~djcrud.views.spa.SPAView` uses ``djcrud/base_spa.html`` and sets
``unpoly_target = 'body'`` for you. Custom SPA shells should follow the same
``*base_spa.html`` naming convention. Menu links on SPA pages always use
``up-follow="false"`` so every hop reloads the full document and exits the SPA
shell cleanly.

View and registration
---------------------

Subclass :py:class:`~djcrud.views.spa.SPAView` and append it to
:data:`djcrud.site` — no model router required. Extend ``class Media`` to append
your ES module paths as :class:`~django.forms.widgets.Script` entries with
``type="module"``.
:attr:`~djcrud.route.Route.urlpath` defaults to the view codename (``spa/`` for
:class:`SpaView`):

.. literalinclude:: ../../src/djcrud_example/spa_example/djcrud.py

Mounting your app
-----------------

There is no ``index.html`` in the frontend package. Django renders
:file:`djcrud/base_spa.html` (sidebar, CSRF, ``{{ view.media }}``); your
bootstrap HTML and client bundle fill in the rest.

Put the mount node on your view — same pattern as ``icon`` or ``tags`` (see
:doc:`../philosophy`):

.. code-block:: python

   mount_element = '<div id="app"></div>'

:file:`djcrud/base_spa.html` renders it inside ``[up-main]`` via
``{{ view.mount_element|safe }}``. Your ES module must query the same element
and attach your framework:

.. literalinclude:: ../../src/djcrud_example/spa_example/frontend/src/main.js

After ``npm run build``, Vite writes the bundle to
``spa_example/static/spa_example/js/app.js``. Django serves it via the
``Script("spa_example/js/app.js", type="module")`` entry in :file:`djcrud.py`.

Authentication
--------------

The HTML shell uses the same rules as every djcrud view:

* **Anonymous users** are redirected to login before the SPA page renders
  (:py:meth:`~djcrud.view.ViewMixin.dispatch`).
* **Logged-in users** must pass :py:meth:`~djcrud.views.spa.SPAView.has_permission`
  (superuser by default, or a grant from :func:`~djcrud.add_perm`).
* **CSRF** meta tags are in ``base_spa.html``; Unpoly picks them up via
  ``unpoly-config.js``.

The Svelte demo calls ``/api/product/`` with ``credentials: 'same-origin'``, so
the browser sends the Django session cookie and DRF accepts the request when the
user is already logged in (requires :doc:`drf`). For token-based clients, use
:doc:`../reference/djcrud_api/index` (``POST /api/login/`` and Bearer auth) —
see the codegen section below.

SPA shell template
------------------

:file:`djcrud/base_spa.html` renders a collapsible sidebar (``is-hidden`` by
default), introspected navigation, CSRF meta tags, the mount node (see
`Mounting your app`_), and ``{{ view.media.css }}`` / ``{{ view.media.js }}``
from the view's :class:`~django.forms.Media` — no inline JavaScript.

Svelte app
----------

Import ``hamburger.js`` and render the burger inside a Bulma ``.navbar`` so span
colors match the standard shell. The component toggles the server-rendered
``#sidebar``:

.. literalinclude:: ../../src/djcrud_example/spa_example/frontend/src/App.svelte

Rebuild the committed bundle after editing Svelte sources:

.. code-block:: bash

   cd src/djcrud_example/spa_example/frontend
   npm ci
   npm run build

Cross-shell navigation
----------------------

Standard djcrud pages swap content inside ``[up-main]``. SPA pages use a
different document shell (no top navbar). When the active view uses a
``base_spa.html`` template, :meth:`~djcrud.view.ViewMixin.unpoly_link_attributes`
returns plain links for every menu item so the browser always full-reloads.

Try it
------

Log in and visit
`http://localhost:8000/spa/ <http://localhost:8000/spa/>`_.
Open the sidebar with the burger, then jump to ``/item/`` or other tutorial apps;
each hop reloads the matching shell.

The SPA demo is tagged with ``navigation`` so it appears in the standard sidebar
too — useful for entering the SPA from a normal page.

Client codegen
--------------

Call your DRF endpoints from the SPA without hand-writing fetch wrappers.
``GET /api/schema/`` describes login and every registered ViewSet — use it as
the single contract for Swagger, Postman, and JavaScript clients.

Export the schema
~~~~~~~~~~~~~~~~~

Offline — no running server:

.. code-block:: bash

   python manage.py spectacular --file openapi.json --format openapi-json

From the SPA frontend package:

.. code-block:: bash

   cd src/djcrud_example/spa_example/frontend
   npm run api:schema

Generate the JavaScript client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The example uses `OpenAPI Generator <https://openapi-generator.tech/>`_ with
the ``javascript`` target (fetch + promises):

.. code-block:: bash

   cd src/djcrud_example/spa_example/frontend
   npm run api:generate

Both steps: ``npm run api``. The generated ``src/api/`` tree is gitignored;
regenerate after model or ViewSet changes.

Example usage
~~~~~~~~~~~~~

.. code-block:: javascript

   import { AuthApi, ProductApi } from "./api/src/index.js";
   import { ApiClient } from "./api/src/ApiClient.js";

   const client = new ApiClient("/api");
   const auth = new AuthApi(client);
   const { token } = await auth.apiLogin({ username: "su", password: "su" });
   client.authentications.BearerAuth.accessToken = token;

   const products = new ProductApi(client);
   const list = await products.productList();

When the user is already logged in via the HTML session (as on ``/spa/``), you
can also call ``/api/product/`` with ``credentials: 'same-origin'`` — see
``spa_example/frontend/src/App.svelte``.

Alternative generators
~~~~~~~~~~~~~~~~~~~~~~

Any OpenAPI 3 toolchain works against ``/api/schema/``. Popular choices:

* `@hey-api/openapi-ts` — fetch-native, pairs well with Vite
* `orval` — hooks and functions (often TypeScript)

Pick one generator; djcrud maintains the schema, not the client output.

Tests
-----

* `tests/test_spa_example.py on GitHub <https://github.com/jpic/djcrud/blob/master/tests/test_spa_example.py>`_
* Browser tests in :file:`tests/test_spa_browser.py` verify full-page transitions
  between the standard shell and the SPA.