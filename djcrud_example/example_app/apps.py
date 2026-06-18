from django.apps import AppConfig


class ExampleAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djcrud_example.example_app'
    label = 'example_app'  # Short label for AUTH_USER_MODEL
