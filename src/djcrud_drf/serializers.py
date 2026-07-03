from rest_framework import serializers


def serializer_for_model(model, fields=None):
    """Return a ModelSerializer class for *model*."""
    meta_fields = fields
    if meta_fields is None:
        meta_fields = [field.name for field in model._meta.fields]

    class Meta:
        pass

    Meta.model = model
    Meta.fields = list(meta_fields)

    return type(
        f"{model.__name__}Serializer",
        (serializers.ModelSerializer,),
        {"Meta": Meta},
    )