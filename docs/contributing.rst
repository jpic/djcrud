Contributing
~~~~~~~~~~~~

djcrud is a Django MVC layer with a Bulma frontend. Most contributors work in
Python; the JavaScript is thin glue over server-rendered HTML, not a separate
frontend application.

- :doc:`Philosophy <philosophy>`
- :doc:`Install <install>`
- :doc:`Tutorial <tutorial/index>`
- :doc:`Reference <reference/index>`

The example project used by tests lives in :file:`src/djcrud_example/`.

Development setup
=================

.. code-block:: bash

   git clone https://github.com/jpic/djcrud.git
   cd djcrud
   pip install --pre -e ".[dev,docs]"
   npm ci   # only needed for JavaScript unit tests

**Browser tests** require Firefox and geckodriver on your ``PATH`` (CI installs
both via ``browser-actions/setup-firefox`` and
``browser-actions/setup-geckodriver``).

**Documentation builds** need the ``[docs]`` extra from :file:`pyproject.toml`
(or :file:`docs/requirements.txt`).

Running tests
=============

Run the same checks as CI before opening a pull request.

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Layer
     - Command
     - Notes
   * - Fast Python
     - ``pytest -m "not splinter" -n auto``
     - Default ``addopts`` in :file:`pyproject.toml` enable parallel runs
   * - Browser (Splinter)
     - ``pytest -m splinter -n 0 --splinter-headless``
     - Must use ``-n 0`` (serial); needs Firefox + geckodriver
   * - Full Python suite
     - ``tox``
     - Runs both commands above
   * - JavaScript (Vitest)
     - ``npm test``
     - happy-dom; see :file:`vitest.config.js`
   * - Tutorial integrity
     - ``pytest -m tutorial -n 0``
     - Validates ``literalinclude`` paths in docs
   * - Doc screenshots
     - see :ref:`updating-screenshots`
     - Always ``-n 0``

Pytest configuration
--------------------

Configuration lives in :file:`pyproject.toml` (``[tool.pytest.ini_options]``).
Tests use the ``djcrud_example`` Django project
(``DJANGO_SETTINGS_MODULE=djcrud_example.settings``).

.. list-table:: Pytest markers
   :header-rows: 1
   :widths: 25 75

   * - Marker
     - Purpose
   * - ``splinter``
     - Browser tests; always run with ``-n 0``
   * - ``docs_screenshot``
     - Captures PNGs into :file:`docs/_static/screenshots/`
   * - ``tutorial``
     - Validates tutorial example apps referenced from docs
   * - ``django_db``
     - Needs database access
   * - ``bulma``
     - Bulma frontend-specific (reserved)

Shared fixtures and helpers
---------------------------

:file:`tests/conftest.py` provides:

- ``_autodiscover_routes`` (autouse) — calls ``djcrud.site.build()`` before each
  test
- ``admin_user`` — pytest-django superuser (``admin`` / ``password``)
- ``browser_login`` — Splinter login helper
- ``many_users``, ``routing_bulk_items`` — seeded data for browser tests

:file:`tests/alight_helpers.py` has DAL/autocomplete helpers for Splinter tests
(``wait_alight_ready``, ``type_and_select``, ``open_autocomplete``, etc.).

Subset examples
---------------

.. code-block:: bash

   pytest tests/test_routing_example.py -v
   pytest tests/test_list_action.py -n 0 --splinter-headless
   npm run test:ui   # optional Vitest UI

Documentation
=============

Docs are **Sphinx** with the Furo theme under :file:`docs/`.

.. code-block:: bash

   make -C docs html
   # preview: docs/_build/html/index.html

CI (``.github/workflows/docs.yml``) runs ``pytest -m tutorial -n 0`` then
``make -C docs html`` on every push and pull request.

**Layout:**

- :file:`docs/tutorial/` — staged tutorial RST files
- :file:`docs/reference/` — API reference
- :file:`docs/_static/screenshots/` — committed PNGs embedded in RST

When editing tutorial code shown via ``.. literalinclude::`` in
:file:`docs/**/*.rst`, keep paths valid — :file:`tests/test_tutorial_docs.py`
fails if a referenced file is missing or moved.

.. _updating-screenshots:

Updating screenshots
====================

There are two screenshot directories. Only one is used in published docs.

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Directory
     - Committed?
     - Purpose
   * - :file:`docs/_static/screenshots/`
     - Yes
     - PNGs embedded in Sphinx via ``.. figure:: /_static/screenshots/<name>.png``
   * - :file:`tests/screenshots/dal/`, :file:`tests/screenshots/topbar/`
     - Yes (debug)
     - Intermediate captures from DAL/topbar Splinter tests; not used in docs

Regenerate all doc screenshots
------------------------------

After changing templates or navigation that appear in the docs:

.. code-block:: bash

   pytest tests/test_docs_screenshots.py tests/test_djcrud_dal_topbar_splinter.py -n0 --splinter-headless
   make -C docs html

Commit the updated PNGs under :file:`docs/_static/screenshots/` with your
change.

Helpers live in :file:`tests/doc_screenshots.py`:

- ``capture(browser, name)`` — writes :file:`docs/_static/screenshots/<name>.png`
- ``prepare_browser(browser)`` — sets viewport to 1280×900
- ``DOC_SCREENSHOTS`` — registry of expected PNG names
- ``assert_all_captured()`` — verifies every registered screenshot exists

**Skip screenshot regeneration** for pure Python changes, doc text-only edits,
or tutorial code changes with no visual impact.

Adding a new doc screenshot
---------------------------

#. Add ``.. figure:: /_static/screenshots/<name>.png`` in the appropriate
   ``.rst`` file.
#. Capture it in :file:`tests/test_docs_screenshots.py` (or an existing Splinter
   test) using ``from doc_screenshots import capture``.
#. Add ``<name>`` to ``DOC_SCREENSHOTS`` in :file:`tests/doc_screenshots.py`.
#. Run the regenerate command above and commit the PNG.

JavaScript for Python developers
================================

djcrud JavaScript manages client-side state and DOM updates within
server-rendered HTML. Python owns permissions, URLs, and markup structure.

.. code-block:: text

   Django view (list_actions, unpoly_attributes)
           ↓
   Django template (custom element tags, data-* hooks)
           ↓
   Static ES module (custom element or up.compiler)
           ↓
   Unpoly partial updates (up:fragment:inserted, compilers)
           ↓
   Vitest (unit) + pytest/Splinter (integration)

Where JavaScript lives
----------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Location
     - Role
   * - :file:`src/djcrud_bulma/static/djcrud_bulma/js/`
     - Core UI components
   * - :file:`src/djcrud_dal_topbar/static/djcrud_dal_topbar/js/`
     - Extension components (e.g. site search)
   * - :file:`src/djcrud_bulma/static/djcrud_bulma/css/style.css`
     - Layout and component styles

Scripts load from :file:`src/djcrud_bulma/templates/djcrud/base.html` as native
ES modules (``type="module"``). There is **no bundler** — files ship via
setuptools ``package-data`` and Django ``{% static %}``.

:file:`package.json` is dev-only (Vitest + happy-dom).

Two patterns
------------

Choose one when adding frontend behavior.

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Pattern
     - When to use
     - Examples
   * - **Custom element** (``HTMLElement``)
     - Interactive UI tied to server-rendered children inside the tag
     - ``<list-action-bar>``, ``<filter-sidebar-toggle>``, ``<hamburger-menu>``
   * - **Unpoly compiler module**
     - Attach behavior when Unpoly compiles new DOM fragments
     - ``form-focus.js``, ``toast.js``, ``nav-config.js``

Custom element conventions
--------------------------

- **No Shadow DOM** — light DOM only. Django renders children inside the tag;
  JS uses ``this.querySelector(...)``.
- Register with a guard so the module is safe to load more than once:

  .. code-block:: javascript

     if (!customElements.get('list-action-bar')) {
         customElements.define('list-action-bar', ListActionBar);
     }

- ``connectedCallback()`` wires listeners; defer init with
  ``queueMicrotask(() => this.init())``.
- ``disconnectedCallback()`` unbinds listeners where needed.
- Listen for ``up:fragment:inserted`` when the feature must survive
  ``[up-list]`` / ``[up-table]`` partial updates (see
  :file:`list-action-bar.js`).
- Config via HTML attributes (``table``, ``scope``, ``target``) and ``data-*``
  hooks (``data-pk``, ``data-role``, ``data-list-action``).
- Export classes and pure helpers for Vitest.
- Expose ``window.djcrud*`` functions when templates or Python need to call JS
  (e.g. ``djcrudClearListActionSelections``).

Some toggles wrap light-DOM children in a ``<button type="button">`` so Bulma
and Unpoly nav feedback do not strip ``is-active`` from ``<a>`` inside
``<nav>`` (see :file:`filter-sidebar.js`, :file:`hamburger.js`).

Unpoly compiler conventions
---------------------------

Compiler modules export a ``register*`` function and auto-register when
``window.up`` exists:

.. code-block:: javascript

   export function registerFormFocus(up) {
       up.compiler('form[method="post"], form.djcrud-filter-form', (form) => {
           queueMicrotask(() => focusFirstInput(form));
       });
   }

   if (typeof window !== 'undefined' && window.up) {
       registerFormFocus(window.up);
   }

Python ↔ JavaScript contract
----------------------------

Templates and JS agree on tags, attributes, and ``data-*`` hooks.

**List action bar** — :file:`src/djcrud_bulma/templates/djcrud/list.html` wraps
bulk actions in ``<list-action-bar>`` and passes i18n labels via
``data-count-label-*`` attributes.

**Python bridge** — :file:`src/djcrud/views/list_action.py`:

- ``ListActionMixin.unpoly_attributes(context='list_action_bar')`` sets
  ``data-list-action="urlupdate"`` and ``up-on-accepted`` calling
  ``djcrudClearListActionSelections()``.
- ``form_attributes`` sets ``up-on-finished='djcrudClearListActionSelections()'``.
- Views with ``tags = ['list_action']`` are discovered for the action bar.

**Templatetags** — :file:`src/djcrud/templatetags/djcrud.py` provides
``unpoly_attributes`` and ``html_attributes`` for wiring Unpoly from Python.

**State persistence** — ``sessionStorage`` with prefixed keys (e.g.
``djcrud:list-action:{scope}?{query}`` for selected row PKs across pagination).

Testing JavaScript changes
--------------------------

#. **Vitest** (fast) — add ``<name>.test.js`` beside the source file; register
   it in :file:`vitest.config.js` ``include``; mock ``up`` where needed.
#. **pytest HTML** (no browser) — assert rendered HTML contains custom element
   tags (e.g. :file:`tests/test_views_example.py`, :file:`tests/test_filter.py`).
#. **pytest Splinter** (integration) — click elements, run
   ``browser.execute_script(...)`` against component APIs (e.g.
   :file:`tests/test_list_action.py`).

Adding a new component
----------------------

#. Pick a pattern (custom element vs ``up.compiler``).
#. Add ``*.js`` under the appropriate :file:`static/.../js/` directory.
#. Include the script in :file:`base.html` or a feature partial.
#. Use the custom element tag and attributes in a Django template.
#. Add Vitest coverage and pytest coverage for user-facing behavior.
#. If the UI appears in docs, add a screenshot capture (see
   :ref:`updating-screenshots`).

Code style
==========

- **Python:** ``black`` and ``ruff``, line length 88 (:file:`pyproject.toml`).
- **JavaScript:** ES modules, no bundler; match existing file style.

Pull request checklist
======================

Before opening a PR:

- [ ] ``pytest -m "not splinter" -n auto``
- [ ] ``pytest -m splinter -n 0 --splinter-headless`` (if UI, templates, or JS
      changed)
- [ ] ``npm test`` (if JavaScript changed)
- [ ] ``pytest -m tutorial -n 0`` and ``make -C docs html`` (if docs or
      tutorial changed)
- [ ] Regenerate and commit doc screenshots (if Bulma UI shown in docs changed)