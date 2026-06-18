from django import template
from django.template.base import token_kwargs, Variable
import uuid

register = template.Library()


@register.simple_tag
def uuid4():
    """Generate a random UUID4 string."""
    return str(uuid.uuid4())


@register.tag(name='eval')
def do_eval(parser, token):
    """
    Template tag that evaluates a callable with arguments and stores the result.

    Usage:
        {% eval obj.method arg1 arg2 kwarg1='value' as result %}
        {% eval my_func 42 'string' as output %}

    This allows calling methods/functions with both positional and keyword
    arguments, similar to Jinja2's call expressions.
    """
    bits = token.split_contents()

    if len(bits) < 4:
        raise template.TemplateSyntaxError(
            "%r tag requires at least 3 arguments: the callable, "
            "optional arguments, and 'as variable_name'" % bits[0]
        )

    tag_name = bits[0]

    # Find 'as' keyword
    try:
        as_index = bits.index('as')
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

    # Parse callable and arguments
    callable_expr = bits[1]
    arg_bits = bits[2:as_index]
    var_name = bits[as_index + 1]

    # Separate positional and keyword arguments
    args = []
    kwargs = {}

    for bit in arg_bits:
        if '=' in bit and not (bit.startswith('"') or bit.startswith("'")):
            # This is a keyword argument
            kwarg_dict = token_kwargs([bit], parser)
            kwargs.update(kwarg_dict)
        else:
            # This is a positional argument
            args.append(parser.compile_filter(bit))

    # Use Variable instead of compile_filter to avoid automatic calling
    callable_var = Variable(callable_expr)

    return EvalNode(callable_var, args, kwargs, var_name)


class EvalNode(template.Node):
    def __init__(self, callable_var, args, kwargs, var_name):
        self.callable_var = callable_var
        self.args = args
        self.kwargs = kwargs
        self.var_name = var_name

    def render(self, context):
        # Manually resolve the variable without calling it
        # This avoids Django's automatic callable handling
        callable_obj = self._resolve_variable_path(self.callable_var, context)

        # Resolve positional arguments
        resolved_args = [arg.resolve(context) for arg in self.args]

        # Resolve keyword arguments
        resolved_kwargs = {
            key: val.resolve(context)
            for key, val in self.kwargs.items()
        }

        # Call the callable with arguments
        try:
            result = callable_obj(*resolved_args, **resolved_kwargs)
        except Exception as e:
            if context.template.engine.debug:
                raise
            result = None

        # Store result in context
        context[self.var_name] = result

        return ''

    def _resolve_variable_path(self, variable, context):
        """
        Resolve a variable path without calling callables at the end.
        This is needed because Django's default Variable.resolve() will
        automatically call callables.

        NOTE: This is a copy/paste of Django's variable resolution logic.
        Ideally, Django would provide a way to disable auto-calling behavior
        (e.g., Variable.resolve(context, auto_call=False) or a separate method).
        This would eliminate the need for this code duplication.

        If you're interested in contributing to Django, this would be a great
        enhancement - see django.template.base.Variable._resolve_lookup() for
        the source of the auto-calling behavior that necessitates this workaround.

        Related: Django has `do_not_call_in_templates` attribute as a workaround,
        but that requires modifying every callable, which isn't practical for
        a general-purpose eval tag.
        """
        current = context

        # Parse the variable path (e.g., 'obj.method' -> ['obj', 'method'])
        parts = variable.var.split('.')

        for i, part in enumerate(parts):
            try:
                # Try dictionary lookup
                current = current[part]
            except (TypeError, KeyError, AttributeError):
                try:
                    # Try attribute lookup
                    current = getattr(current, part)
                except AttributeError:
                    try:
                        # Try list index
                        current = current[int(part)]
                    except (ValueError, KeyError, TypeError, IndexError):
                        return ''

            # Only call callables if they're not the final part
            # (the final part is what we want to call ourselves with args)
            if callable(current) and i < len(parts) - 1:
                try:
                    current = current()
                except TypeError:
                    # Callable requires arguments, can't auto-call
                    pass

        return current
