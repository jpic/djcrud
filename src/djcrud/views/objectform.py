from django.utils.html import format_html
from django.utils.translation import gettext as _

from .. import tags
from ..model import ModelMixin
from .action import ActionMixin, ObjectPermissionMixin
from .log import CHANGE
from .object import ObjectMixin
from .form import FormMixin, FormView
from .modelform import ModelFormMixin


class ObjectFormMixin(ObjectMixin, ModelMixin, FormMixin):
    """Form bound to :attr:`~djcrud.views.object.ObjectMixin.object`."""

    def get_form_valid_message(self):
        opts = self.model._meta
        obj = self.object
        get_absolute_url = getattr(obj, "get_absolute_url", None)
        if callable(get_absolute_url):
            obj = format_html(
                '<a href="{}">{}</a>',
                get_absolute_url(),
                obj,
            )
        return _('The {name} "{obj}" was changed successfully.').format(
            name=opts.verbose_name,
            obj=obj,
        )


class ObjectFormView(ActionMixin, ObjectPermissionMixin, ObjectFormMixin, FormView):
    """Object-bound form action opened from the object menu."""

    tags = [tags.OBJECT]


class ObjectModelFormMixin(ObjectMixin, ModelFormMixin):
    """Model form for updating :attr:`~djcrud.views.object.ObjectMixin.object`."""

    log_action_flag = CHANGE

    def get_form_valid_message(self):
        opts = self.model._meta
        return _('The {name} "{obj}" was changed successfully.').format(
            name=opts.verbose_name,
            obj=self.object,
        )
