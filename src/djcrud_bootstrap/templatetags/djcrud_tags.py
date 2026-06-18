"""
Template tags for djcrud_bootstrap.
"""

from django import template

register = template.Library()


@register.filter
def get_model_fields(obj):
    """
    Get all fields from a model instance for display in detail view.

    Returns a list of dicts with 'label' and 'value' keys.
    """
    if not obj:
        return []

    fields = []
    meta = obj._meta

    for field in meta.get_fields():
        # Skip reverse relations
        if field.auto_created and not field.concrete:
            continue

        # Get field value
        try:
            value = getattr(obj, field.name)

            # Format value
            if value is None:
                value = '-'
            elif hasattr(value, 'all'):  # ManyToMany
                value = ', '.join(str(v) for v in value.all())
            else:
                value = str(value)

            fields.append({
                'label': field.verbose_name.capitalize() if hasattr(field, 'verbose_name') else field.name,
                'value': value,
            })
        except AttributeError:
            continue

    return fields
