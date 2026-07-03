"""Static asset bundles for djcrud Bulma shells.

Views expose Django :class:`~django.forms.Media` (see
:class:`~djcrud.views.spa.SPAView`). Templates render ``{{ view.media.css }}``
in ``<head>`` and ``{{ view.media.js }}`` before ``</body>`` — no inline
JavaScript in the reference templates. ES modules use
:class:`~django.forms.widgets.Script` with ``type="module"`` (Django 6+).
"""

from django.forms.widgets import Script

BULMA_CSS = (
    "https://cdn.jsdelivr.net/npm/bulma@1.0.2/css/bulma.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css",
    "https://unpkg.com/unpoly@3.9.2/unpoly.css",
    "djcrud_bulma/css/style.css",
)

UNPOLY_JS = "https://unpkg.com/unpoly@3.9.2/unpoly.js"

# ES modules — load :data:`UNPOLY_JS` as a classic <script> before these.
_SHELL_JS = (
    Script("djcrud_bulma/js/unpoly-config.js", type="module"),
    Script("djcrud_bulma/js/nav-config.js", type="module"),
)


class SpaShellMedia:
    """Assets for :class:`~djcrud.views.spa.SPAView` (sidebar + client mount)."""

    css = {"all": BULMA_CSS}
    js = _SHELL_JS


class StandardShellMedia:
    """Assets for the standard ``djcrud/base.html`` shell."""

    css = {"all": BULMA_CSS}
    js = _SHELL_JS + (
        Script("djcrud_bulma/js/hamburger.js", type="module"),
        Script("djcrud_bulma/js/form-focus.js", type="module"),
        Script("djcrud_bulma/js/filter-sidebar.js", type="module"),
        Script("djcrud_bulma/js/list-action-bar.js", type="module"),
        Script("djcrud_bulma/js/toast.js", type="module"),
    )
