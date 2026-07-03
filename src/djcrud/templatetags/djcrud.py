"""djcrud template tags and filters.

Load in templates with ``{% load djcrud %}``.

Filters:
    :func:`html_attributes` — render a dict as safe HTML attributes.
    :func:`unpoly_attributes` — call
    :meth:`~djcrud.view.ViewMixin.unpoly_attributes` on a view for a rendering
    context.

Tags:
    :func:`do_eval` — ``{% eval %}``; call a view method and store the result.
"""

import re

from django import template
from django.template.base import token_kwargs, Variable
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

SAFE_ATTR_NAME = re.compile(r"^[a-zA-Z][\w-]*$")
_MISSING = object()


@register.filter
def html_attributes(attrs):
    """Render *attrs* as a safe HTML attribute string.

    Boolean ``True`` renders as a boolean attribute (name only). ``False``
    renders as ``name="false"``. Other values are escaped and quoted. Keys that
    do not match a safe attribute name pattern are skipped.

    Example::

        {{ view.form_attributes|html_attributes }}
        {{ action|unpoly_attributes:'model_menu'|html_attributes }}
    """
    if not attrs:
        return ""
    parts = []
    for key, value in attrs.items():
        if not SAFE_ATTR_NAME.match(key):
            continue
        if value is True:
            parts.append(key)
        elif value is False:
            parts.append(f'{key}="false"')
        else:
            parts.append(f'{key}="{escape(value)}"')
    return mark_safe(" ".join(parts))


@register.filter
def unpoly_attributes(target_view, context=""):
    """Return Unpoly link attributes for *target_view* in *context*.

    When the active page view is available on ``request._djcrud_view``, delegates
    to :meth:`~djcrud.view.ViewMixin.unpoly_link_attributes` so shell changes
    trigger a plain reload via :data:`~djcrud.redirect.FULL_PAGE_LINK_ATTRIBUTES`.
    Otherwise falls back to :meth:`~djcrud.view.ViewMixin.unpoly_attributes` on
    *target_view*.

    Pair with :func:`html_attributes` in templates::

        {{ action|unpoly_attributes:'model_menu'|html_attributes }}
    """
    link_context = context or None
    request = getattr(target_view, "request", None)
    current_view = getattr(request, "_djcrud_view", None) if request else None
    if current_view is not None and hasattr(current_view, "unpoly_link_attributes"):
        return current_view.unpoly_link_attributes(target_view, link_context)
    fn = getattr(target_view, "unpoly_attributes", None)
    if fn is None:
        return {}
    return fn(link_context)


@register.tag(name="eval")
def do_eval(parser, token):
    """``{% eval %}`` template tag — call a callable and assign the result.

    Syntax::

        {% eval callable positional_arg keyword=value as variable_name %}

    *callable* is a template variable path (for example ``view.pagination_url``).
    Positional and keyword arguments are resolved in the template context and
    passed to the callable. The return value is stored in *variable_name* for
    the remainder of the template.

    Example::

        {% load djcrud %}
        {% eval view.pagination_url 2 as url %}
        <a href="{{ url }}">Page 2</a>

        {% eval view.some_method "arg" user=view.request.user as result %}
    """
    bits = token.split_contents()

    if len(bits) < 4:
        raise template.TemplateSyntaxError(
            "%r tag requires at least 3 arguments: the callable, "
            "optional arguments, and 'as variable_name'" % bits[0]
        )

    tag_name = bits[0]

    try:
        as_index = bits.index("as")
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires 'as variable_name' at the end" % tag_name
        )

    if as_index < 2:
        raise template.TemplateSyntaxError(
            "%r tag requires a callable before 'as'" % tag_name
        )

    if as_index >= len(bits) - 1:
        raise template.TemplateSyntaxError(
            "%r tag requires a variable name after 'as'" % tag_name
        )

    callable_expr = bits[1]
    arg_bits = bits[2:as_index]
    var_name = bits[as_index + 1]

    args = []
    kwargs = {}

    for bit in arg_bits:
        if "=" in bit and not (bit.startswith('"') or bit.startswith("'")):
            kwarg_dict = token_kwargs([bit], parser)
            kwargs.update(kwarg_dict)
        else:
            args.append(parser.compile_filter(bit))

    callable_var = Variable(callable_expr)

    return EvalNode(callable_var, args, kwargs, var_name)


class EvalNode(template.Node):
    """Parse tree node for :func:`do_eval`."""

    def __init__(self, callable_var, args, kwargs, var_name):
        self.callable_var = callable_var
        self.args = args
        self.kwargs = kwargs
        self.var_name = var_name

    def render(self, context):
        callable_obj = self._resolve_variable_path(self.callable_var, context)

        resolved_args = [arg.resolve(context) for arg in self.args]

        resolved_kwargs = {
            key: val.resolve(context) for key, val in self.kwargs.items()
        }

        if callable_obj is _MISSING:
            result = None
        elif callable(callable_obj):
            try:
                result = callable_obj(*resolved_args, **resolved_kwargs)
            except Exception:
                if context.template.engine.debug:
                    raise
                result = None
        else:
            result = callable_obj

        context[self.var_name] = result

        return ""

    def _resolve_variable_path(self, variable, context):
        current = context

        parts = variable.var.split(".")

        for i, part in enumerate(parts):
            try:
                current = current[part]
            except (TypeError, KeyError, AttributeError):
                try:
                    current = getattr(current, part)
                except AttributeError:
                    try:
                        current = current[int(part)]
                    except (ValueError, KeyError, TypeError, IndexError):
                        return _MISSING

            if callable(current) and i < len(parts) - 1:
                try:
                    current = current()
                except TypeError:
                    pass

        return current
