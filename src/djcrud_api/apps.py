from django.apps import AppConfig


class DjcrudApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djcrud_api"
    verbose_name = "djcrud API"

    def ready(self):
        import djcrud_api.models  # noqa: F401
