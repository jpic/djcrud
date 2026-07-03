from django.apps import AppConfig
from django.conf import settings


class DjcrudBulmaConfig(AppConfig):
    name = "djcrud_bulma"

    def ready(self):
        settings.CRISPY_TEMPLATE_PACK = getattr(
            settings, "CRISPY_TEMPLATE_PACK", "bulma"
        )
        # Ensure "bulma" is allowed (prevents TemplateDoesNotExist; crispy_forms defaults to uni_form).
        if not hasattr(settings, "CRISPY_ALLOWED_TEMPLATE_PACKS"):
            settings.CRISPY_ALLOWED_TEMPLATE_PACKS = ("bulma",)
