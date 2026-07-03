from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class DjcrudDalConfig(AppConfig):
    name = "djcrud_dal"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        for app in ("dal", "dal_alight", "queryset_sequence", "dal_queryset_sequence"):
            if app not in settings.INSTALLED_APPS:
                raise ImproperlyConfigured(
                    f"djcrud_dal requires {app!r} in INSTALLED_APPS"
                )
        try:
            import djhacker  # noqa: F401
        except ImportError as exc:
            raise ImproperlyConfigured(
                "djcrud_dal requires djhacker to be installed"
            ) from exc

        import djcrud_dal.models  # noqa: F401
        from . import hooks  # noqa: F401

        hooks.register()
