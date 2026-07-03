"""Static asset bundles for djcrud Bulma shells.

Views expose these through :class:`ModuleMedia` (see
:class:`~djcrud.views.spa.SPAView`). Templates render ``{{ view.media.css }}``
in ``<head>`` and ``{{ view.media.js }}`` before ``</body>`` — no inline
JavaScript in the reference templates.
"""

from django.forms import Media
from django.utils.html import format_html


class ModuleMedia(Media):
    """Like :class:`~django.forms.Media`, but ES module ``<script>`` tags."""

    def render_js(self):
        return [
            (
                path.__html__()
                if hasattr(path, "__html__")
                else format_html(
                    '<script type="module" src="{}"></script>',
                    self.absolute_path(path),
                )
            )
            for path in self._js
        ]

BULMA_CSS = (
    "https://cdn.jsdelivr.net/npm/bulma@1.0.2/css/bulma.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css",
    "https://unpkg.com/unpoly@3.9.2/unpoly.css",
    "djcrud_bulma/css/style.css",
)

UNPOLY_JS = "https://unpkg.com/unpoly@3.9.2/unpoly.js"

# ES modules only — load :data:`UNPOLY_JS` as a classic <script> before these.
_SHELL_JS = (
    "djcrud_bulma/js/unpoly-config.js",
    "djcrud_bulma/js/nav-config.js",
)


class SpaShellMedia:
    """Assets for :class:`~djcrud.views.spa.SPAView` (sidebar + client mount)."""

    css = {"all": BULMA_CSS}
    js = _SHELL_JS


class StandardShellMedia:
    """Assets for the standard ``djcrud/base.html`` shell."""

    css = {"all": BULMA_CSS}
    js = _SHELL_JS + (
        "djcrud_bulma/js/hamburger.js",
        "djcrud_bulma/js/form-focus.js",
        "djcrud_bulma/js/filter-sidebar.js",
        "djcrud_bulma/js/list-action-bar.js",
        "djcrud_bulma/js/toast.js",
    )