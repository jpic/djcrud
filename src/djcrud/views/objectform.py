from django.utils.translation import gettext as _

from ..model import ModelMixin
from .log import CHANGE
from .object import ObjectMixin
from .form import FormMixin
from .modelform import ModelFormMixin


class ObjectFormMixin(ObjectMixin, ModelMixin, FormMixin):
    """Form bound to :attr:`~djcrud.views.object.ObjectMixin.object`."""

    def get_form_valid_message(self):
        opts = self.model._meta
        return _('The {name} "{obj}" was changed successfully.').format(
            name=opts.verbose_name,
            obj=self.object,
        )


class ObjectModelFormMixin(ObjectMixin, ModelFormMixin):
    """Model form for updating :attr:`~djcrud.views.object.ObjectMixin.object`."""

    log_action_flag = CHANGE

    def get_form_valid_message(self):
        opts = self.model._meta
        return _('The {name} "{obj}" was changed successfully.').format(
            name=opts.verbose_name,
            obj=self.object,
        )
