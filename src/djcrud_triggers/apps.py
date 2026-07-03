from django.apps import AppConfig


class DjcrudTriggersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djcrud_triggers"
    verbose_name = "Trigger hooks"

    def ready(self) -> None:
        from djcrud_triggers.hooks import register_hook

        register_hook("gateway:startup", self._noop_hook, app=self.name)

    @staticmethod
    def _noop_hook(event):
        return None

    @staticmethod
    def _skip_hook(event):
        from djcrud_triggers.hooks import HookDecision, TriggerHookResult

        return TriggerHookResult(decision=HookDecision.SKIP, reason="busy")
