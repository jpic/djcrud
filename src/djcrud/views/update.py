from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.views import generic

from .action import ActionMixin
from .objectform import ObjectModelFormMixin
from .template import TemplateViewMixin


class UpdateView(
    ActionMixin,
    ObjectModelFormMixin,
    TemplateViewMixin,
    generic.UpdateView,
):
    """Update an existing model instance.

    Attributes:
        permission_shortcode (str): Default ``'change'``.
        tags (list[str]): Default ``['object']`` (object action menu).
        default_template_name (str): Form template.
        icon (str): Bootstrap Icons name.
        color (str): Bulma button colour modifier.
        fields (list[str]): Model form fields. Set on clone or subclass.
        form_class (type): Explicit form class instead of ``fields``.
    """

    permission_shortcode = "change"
    tags = ["object"]
    default_template_name = "form.html"
    icon = "pencil"
    color = "warning"

    @property
    def title(self):
        return _("Change %(name)s") % {
            "name": capfirst(self.model._meta.verbose_name),
        }