from django.apps import AppConfig
from django.conf import settings


class DjcrudBootstrapConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djcrud_bootstrap"
    verbose_name = "djcrud Bootstrap Frontend"

    def ready(self):
        """Auto-detect and configure based on which frontend is installed.

        Sets DJCRUD_FRONTEND automatically (no manual setting required in most cases).
        Supports `pip install djcrud[bootstrap]`.
        If both frontends are installed, the last AppConfig to run wins (order in INSTALLED_APPS).
        Set DJCRUD_FRONTEND manually to override.
        """
        # Auto-set if not already in settings (manual DJCRUD_FRONTEND in settings.py takes precedence).
        # (Bootstrap ready() runs after Bulma if both in INSTALLED_APPS.)
        if getattr(settings, "DJCRUD_FRONTEND", None) is None:
            settings.DJCRUD_FRONTEND = "djcrud_bootstrap"

        # Bootstrap 5 frontend (requires crispy-bootstrap5). Only set CRISPY_TEMPLATE_PACK.
        settings.CRISPY_TEMPLATE_PACK = getattr(
            settings, "CRISPY_TEMPLATE_PACK", "bootstrap5"
        )
        settings.DJCRUD_TABLES2_TEMPLATE = getattr(
            settings,
            "DJCRUD_TABLES2_TEMPLATE",
            "django_tables2/bootstrap5.html",
        )
