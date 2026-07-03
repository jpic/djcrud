import functools

from django.contrib.admin.utils import NestedObjects
from django.db import router
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext as _, gettext_lazy
from django.views import generic

from .. import tags
from .action import ActionMixin, ObjectPermissionMixin
from .form import FormView
from .list_action import ListActionMixin
from .log import DELETION, LogMixin
from .template import TemplateViewMixin
from .objectform import ObjectFormMixin

DELETE_CONFIRM_SINGLE = gettext_lazy(
    'Are you sure you want to delete the %(object_name)s "%(escaped_object)s"? '
    "All of the following related items will be deleted:"
)

DELETE_CONFIRM_BULK = gettext_lazy(
    "Are you sure you want to delete the selected %(objects_name)s? All of the "
    "following objects and their related items will be deleted:"
)


def get_deleted_objects(view, objs):
    """
    Find objects related to ``objs`` that would be deleted (cascade).

    Return a tuple of ``(nested_objects, model_count, protected)``.
    """
    try:
        obj = objs[0]
    except (IndexError, TypeError):
        return [], {}, []

    if hasattr(objs, "exists") and not objs.exists():
        return [], {}, []

    using = router.db_for_write(obj._meta.model)
    collector = NestedObjects(using=using, origin=objs)
    collector.collect(objs)

    def format_callback(obj):
        opts = obj._meta
        label = capfirst(opts.verbose_name)
        detail_urlname = getattr(view, "detail_urlname", None)
        if obj._meta.model == view.model and detail_urlname:
            try:
                url = reverse(detail_urlname, args=[obj.pk])
            except NoReverseMatch:
                return f"{label}: {obj}"
            return format_html(
                '{}: <a href="{}" up-layer="new modal" up-size="large" up-history="false">{}</a>',
                label,
                url,
                obj,
            )
        return f"{label}: {obj}"

    to_delete = collector.nested(format_callback)
    protected = [format_callback(obj) for obj in collector.protected]
    model_count = {
        capfirst(model._meta.verbose_name_plural): len(model_objs)
        for model, model_objs in collector.model_objs.items()
    }
    return to_delete, model_count, protected


class DeleteMixin(ActionMixin, LogMixin):
    """Single-object and bulk delete confirmation.

    Compose concrete subclasses with :class:`~djcrud.views.action.ObjectPermissionMixin`
    (DeleteView) or rely on :class:`~djcrud.views.list_action.ListActionMixin`
    (which brings in :class:`~djcrud.views.action.ObjectListPermissionMixin`)
    for DeleteObjectsView. This ensures per-target permission checks via
    ActionMixin.

    Attributes:
        permission_shortcode (str): Django permission prefix. Default
            ``'delete'``.
        default_template_name (str): Delete confirmation template.
        icon (str): Bootstrap Icons name for action buttons.
        color (str): Bulma button colour modifier.
        log_action_flag (int): ``LogEntry`` action flag when history is enabled.
    """

    permission_shortcode = "delete"
    default_template_name = "djcrud/form_delete.html"
    icon = "trash"
    color = "danger"
    log_action_flag = DELETION

    @property
    def submit_button_label(self):
        return _("Delete")

    @functools.cached_property
    def detail_urlname(self):
        detail_route = self.router.find_route("detail")
        if detail_route is None:
            return None
        return type(detail_route)(request=self.request).urlfullname

    @functools.cached_property
    def deletion_targets(self):
        if hasattr(self, "object_list"):
            return self.object_list
        if getattr(self, "object", None) is not None:
            return self.model._default_manager.filter(pk=self.object.pk)
        return self.model._default_manager.none()

    @functools.cached_property
    def _deletion_info(self):
        return get_deleted_objects(self, self.deletion_targets)

    @property
    def deleted_objects(self):
        return self._deletion_info[0]

    @property
    def deletion_summary(self):
        return self._deletion_info[1].items()

    @property
    def deletion_protected(self):
        return self._deletion_info[2]

    @property
    def has_deletion_cascade(self):
        model_count = self._deletion_info[1]
        if len(model_count) > 1:
            return True
        target_count = self.deletion_targets.count()
        return sum(model_count.values()) > target_count

    @property
    def can_confirm_delete(self):
        return not self.deletion_protected

    @property
    def deletion_protected_message(self):
        if hasattr(self, "object_list"):
            return _(
                "Deleting the selected %(objects_name)s would require deleting "
                "the following protected related objects:"
            ) % {
                "objects_name": capfirst(self.model._meta.verbose_name_plural),
            }
        opts = self.object._meta
        return _(
            'Deleting the %(object_name)s "%(escaped_object)s" would require '
            "deleting the following protected related objects:"
        ) % {
            "object_name": capfirst(opts.verbose_name),
            "escaped_object": self.object,
        }

    def form_valid(self, form):
        for obj in self.get_log_objects():
            if getattr(obj, "pk", None) is not None:
                obj._log_pk = obj.pk
        response = super().form_valid(form)
        self.log_insert()
        return response


class DeleteView(
    DeleteMixin,
    ObjectPermissionMixin,
    ObjectFormMixin,
    TemplateViewMixin,
    generic.DeleteView,
):
    """Confirm and delete a single object."""

    tags = [tags.OBJECT]

    @property
    def title(self):
        return _("Delete")

    @property
    def message(self):
        opts = self.object._meta
        return DELETE_CONFIRM_SINGLE % {
            "object_name": capfirst(opts.verbose_name),
            "escaped_object": self.object,
        }

    def get_form_valid_message(self):
        opts = self.object._meta
        return _('The %(name)s "%(obj)s" was deleted successfully.') % {
            "name": opts.verbose_name,
            "obj": self.object,
        }

    def form_valid(self, form):
        if not self.can_confirm_delete:
            return self.form_invalid(form)
        self.log_objects = [self.object]
        return super().form_valid(form)


class DeleteObjectsView(DeleteMixin, ListActionMixin, FormView):
    """Bulk delete for rows selected on the list view."""

    @property
    def message(self):
        return DELETE_CONFIRM_BULK % {
            "objects_name": capfirst(self.model._meta.verbose_name_plural),
        }

    @property
    def title(self):
        return _("Delete")

    def get_form_valid_message(self):
        count = self._deleted_count
        if count == 1:
            items = capfirst(self.model._meta.verbose_name)
        else:
            items = capfirst(self.model._meta.verbose_name_plural)
        return _("Successfully deleted %(count)d %(items)s.") % {
            "count": count,
            "items": items,
        }

    def form_valid(self, form):
        if not self.can_confirm_delete:
            return self.form_invalid(form)
        self.log_objects = list(self.object_list)
        self._deleted_count = self.object_list.count()
        self.object_list.delete()
        return super().form_valid(form)
