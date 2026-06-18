from django.apps import AppConfig
from django.conf import settings


class DjcrudBulmaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djcrud_bulma"
    verbose_name = "djcrud Bulma Frontend"

    def ready(self):
        """Auto-detect and configure based on which frontend is installed.

        Sets DJCRUD_FRONTEND automatically (no manual setting required in most cases).
        Supports `pip install djcrud[bulma]` or `djcrud[bootstrap]`.
        If both frontends are installed, the last AppConfig to run wins (order in INSTALLED_APPS).
        Set DJCRUD_FRONTEND manually to override.
        """
        # Auto-set if not already in settings (manual DJCRUD_FRONTEND in settings.py takes precedence).
        # Use override_settings(DJCRUD_FRONTEND=...) in tests to simulate different frontends.
        if getattr(settings, "DJCRUD_FRONTEND", None) is None:
            settings.DJCRUD_FRONTEND = "djcrud_bulma"

        # Rely exclusively on crispy-bulma package templates (CRISPY_TEMPLATE_PACK="bulma").
        # No custom templates in djcrud_bulma/templates/bulma/ (deleted to avoid HTML duplication).
        # {{ form|crispy }} now uses crispy_bulma/templates/bulma/uni_form.html, field.html, layout/* etc.
        # This completely removes any reliance on legacy uni_form or custom overrides.
        # Note: crispy_bulma must be in INSTALLED_APPS (via [bulma] extra or tests/settings.py).
        settings.CRISPY_TEMPLATE_PACK = getattr(
            settings, "CRISPY_TEMPLATE_PACK", "bulma"
        )
        # Ensure "bulma" is allowed (prevents TemplateDoesNotExist; crispy_forms defaults to uni_form).
        if not hasattr(settings, "CRISPY_ALLOWED_TEMPLATE_PACKS"):
            settings.CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap5", "bulma")
        settings.DJCRUD_TABLES2_TEMPLATE = getattr(
            settings,
            "DJCRUD_TABLES2_TEMPLATE",
            "django_tables2/bulma.html",
        )
        # Table classes (is-striped etc.) now hardcoded in django_tables2/bulma.html per Bulma docs.
        # No longer uses DJCRUD_TABLES2_ATTRS (removed to minimize settings).
