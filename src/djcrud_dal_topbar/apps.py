from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class DjcrudDalTopbarConfig(AppConfig):
    name = "djcrud_dal_topbar"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        for app in (
            "djcrud_dal",
            "dal_alight",
            "queryset_sequence",
            "dal_queryset_sequence",
        ):
            if app not in settings.INSTALLED_APPS:
                raise ImproperlyConfigured(
                    f"djcrud_dal_topbar requires {app!r} in INSTALLED_APPS"
                )
