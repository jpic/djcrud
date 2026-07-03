import json

from django.apps import apps
from django.utils.html import format_html, mark_safe

# django.contrib.admin.models
ADDITION = 1
CHANGE = 2
DELETION = 3


def log(user, flag, message, obj=None):
    if not apps.is_installed("django.contrib.admin"):
        return None

    from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry

    flag = {"create": ADDITION, "update": CHANGE, "delete": DELETION}.get(flag, flag)
    change_message = json.dumps(message) if isinstance(message, dict) else message
    if not obj:
        return None

    pk = obj.pk if obj.pk is not None else getattr(obj, "_log_pk", None)
    if pk is None:
        return None
    if obj.pk is None:
        obj.pk = pk

    return LogEntry.objects.log_actions(
        user.pk,
        [obj],
        flag,
        change_message,
        single_object=True,
    )


def _format_change_submessage(sub_message):
    from django.contrib.admin.models import LogEntry

    if not isinstance(sub_message, dict):
        return str(sub_message)

    try:
        return LogEntry(change_message=json.dumps([sub_message])).get_change_message()
    except (KeyError, TypeError):
        if changed := sub_message.get("changed"):
            if isinstance(changed, dict) and "fields" not in changed:
                details = []
                for field_name, values in changed.items():
                    if isinstance(values, list) and len(values) == 2:
                        old, new = values
                        if old == "":
                            details.append(
                                format_html("{}: set to {}", field_name, new)
                            )
                        elif new == "":
                            details.append(format_html("{}: cleared", field_name))
                        else:
                            details.append(
                                format_html("{}: {} → {}", field_name, old, new)
                            )
                    else:
                        details.append(format_html("{}: {}", field_name, values))
                if details:
                    return format_html(
                        "Changed {}.", ", ".join(str(d) for d in details)
                    )
        return ""


def _format_admin_changes(changes):
    if not changes:
        return ""

    if not isinstance(changes, list):
        return _format_change_submessage(changes)

    parts = [
        part
        for sub_message in changes
        if (part := _format_change_submessage(sub_message))
    ]
    return " ".join(str(part) for part in parts)


def format_logentry_message(value):
    if not value:
        return ""

    if isinstance(value, str):
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    else:
        data = value

    if isinstance(data, list):
        return _format_admin_changes(data)

    if not isinstance(data, dict):
        return str(data)

    parts = []
    if label := data.get("label"):
        parts.append(format_html("<strong>{}</strong>", label))
    if changes := data.get("changes"):
        parts.append(_format_admin_changes(changes))
    if extra := data.get("extra"):
        if view := extra.get("view"):
            parts.append(format_html('<small class="has-text-grey">{}</small>', view))

    if not parts:
        return ""

    return mark_safe("<br>".join(str(part) for part in parts))


class LogMixin:
    """Write ``LogEntry`` rows when ``djcrud_history`` is installed.

    Attributes:
        log_action_flag (int | bool): ``LogEntry`` action constant, or ``False``
            to skip logging.
    """

    log_action_flag = False

    def get_log_message(self):
        """Short label stored in the log entry."""
        return self.title

    def get_log_extra(self):
        """Extra metadata (view class name, request path) for the log entry."""
        return {
            "view": type(self).__name__,
            "path": self.request.path,
        }

    def get_log_objects(self):
        """Model instances to attach to the log entry."""
        if log_objects := getattr(self, "log_objects", None):
            return log_objects
        if hasattr(self, "object_list"):
            return self.object_list
        if obj := getattr(self, "object", None):
            return [obj]
        return []

    def build_change_message(self):
        from django.contrib.admin.utils import construct_change_message

        envelope = {
            "label": self.get_log_message(),
            "extra": self.get_log_extra(),
        }

        form = getattr(self, "form", None)
        if self.log_action_flag == CHANGE and form is not None:
            changes = construct_change_message(form, [], add=False)
            if changes:
                envelope["changes"] = changes
        elif self.log_action_flag == ADDITION:
            if form is not None:
                envelope["changes"] = construct_change_message(form, [], add=True)
            else:
                envelope["changes"] = [{"added": {}}]

        return envelope

    def log_insert(self):
        """Write log entries for :meth:`get_log_objects` when history is enabled."""
        if not apps.is_installed("django.contrib.admin"):
            return

        if not self.log_action_flag:
            return

        if not self.request.user.is_authenticated:
            return

        message = self.build_change_message()
        for obj in self.get_log_objects():
            log(
                self.request.user,
                self.log_action_flag,
                message,
                obj,
            )
