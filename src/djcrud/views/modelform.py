from django.forms import modelform_factory
from django.utils.translation import gettext as _

from ..model import ModelMixin
from .form import FormMixin
from .log import LogMixin


class ModelFormMixin(LogMixin, ModelMixin, FormMixin):
    """Build a ``ModelForm`` from :attr:`fields` or :attr:`form_class`.

    Attributes:
        fields (list[str] | str): Model form fields, or ``'__all__'``.
        form_class (type): Explicit form class instead of auto-generated form.
    """

    fields = "__all__"

    def get_form_valid_message(self):
        """Success message after creating a model instance."""
        opts = self.model._meta
        return _('The {name} "{obj}" was added successfully.').format(
            name=opts.verbose_name,
            obj=self.form.instance,
        )

    def get_form_class(self):
        """Return :attr:`form_class` or a factory from :attr:`fields`."""
        if getattr(self, "form_class", None):
            return self.form_class
        return modelform_factory(self.model, fields=self.fields)

    def form_valid(self, form):
        """Log creation when :class:`~djcrud.views.log.LogMixin` is active."""
        response = super().form_valid(form)
        self.log_insert()
        return response
