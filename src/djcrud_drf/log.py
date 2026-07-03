from django.apps import apps

from djcrud.views.log import ADDITION, CHANGE, DELETION, log


def serializer_changed_field_labels(serializer):
    """Return verbose field labels that differ in *serializer* validated data."""
    labels = []
    instance = serializer.instance
    for field_name, new_value in serializer.validated_data.items():
        old_value = getattr(instance, field_name)
        if old_value != new_value:
            field = serializer.fields.get(field_name)
            labels.append(str(field.label) if field is not None else field_name)
    return labels


class LogMixin:
    """Write ``LogEntry`` rows for create, update, and destroy actions.

    Attributes:
        log_actions (bool | frozenset[str]): ``True`` logs create, update, and
            destroy; ``False`` disables logging; a frozenset limits which
            actions are logged (``"update"`` covers ``partial_update``).
    """

    log_actions = True

    def get_log_message(self):
        """Short label stored in the log entry."""
        return str(self.model._meta.verbose_name)

    def get_log_extra(self):
        """Extra metadata (view class name, request path) for the log entry."""
        return {
            "view": type(self).__name__,
            "path": self.request.path,
        }

    def _log_action_name(self):
        if self.action == "partial_update":
            return "update"
        return self.action

    def _should_log(self):
        log_actions = self.log_actions
        if log_actions is False:
            return False
        if log_actions is True:
            return True
        return self._log_action_name() in log_actions

    def build_change_message(self, action_flag, changed_fields=None):
        envelope = {
            "label": self.get_log_message(),
            "extra": self.get_log_extra(),
        }
        if action_flag == CHANGE and changed_fields:
            envelope["changes"] = [{"changed": {"fields": changed_fields}}]
        elif action_flag == ADDITION:
            envelope["changes"] = [{"added": {}}]
        return envelope

    def log_insert(self, action_flag, obj, changed_fields=None):
        """Write a log entry for *obj* when audit logging is enabled."""
        if not apps.is_installed("django.contrib.admin"):
            return

        if not self._should_log():
            return

        if not self.request.user.is_authenticated:
            return

        message = self.build_change_message(
            action_flag,
            changed_fields=changed_fields,
        )
        log(self.request.user, action_flag, message, obj)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self.log_insert(ADDITION, serializer.instance)

    def perform_update(self, serializer):
        changed_fields = serializer_changed_field_labels(serializer)
        super().perform_update(serializer)
        self.log_insert(CHANGE, serializer.instance, changed_fields=changed_fields)

    def perform_destroy(self, instance):
        if instance.pk is not None:
            instance._log_pk = instance.pk
        super().perform_destroy(instance)
        self.log_insert(DELETION, instance)