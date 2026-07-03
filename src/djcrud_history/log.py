from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def logentries_for(model, pk):
    from django.contrib.admin.models import LogEntry

    filters = Q(
        content_type=ContentType.objects.get_for_model(model),
        object_id=str(pk),
    )
    name = ".".join(
        [
            model._meta.app_label,
            model._meta.model_name,
        ]
    )
    if name.lower() == settings.AUTH_USER_MODEL.lower():
        filters |= Q(user_id=pk)
    return LogEntry.objects.filter(filters).order_by("-action_time")
