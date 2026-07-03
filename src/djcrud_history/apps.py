from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class DjcrudHistoryConfig(AppConfig):
    name = "djcrud_history"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        if "django.contrib.admin" not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "djcrud_history requires django.contrib.admin in INSTALLED_APPS"
            )
        import djcrud_history.models  # noqa: F401
