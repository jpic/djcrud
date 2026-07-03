def spectacular_settings(**overrides):
    """Return :data:`~django.conf.settings.SPECTACULAR_SETTINGS` with Bearer auth.

    Merges djcrud defaults with *overrides*. Use in ``settings.py``:

    .. code-block:: python

       SPECTACULAR_SETTINGS = djcrud_drf.spectacular_settings(TITLE="My API")
    """
    settings = {
        "TITLE": "djcrud API",
        "VERSION": "1.0.0",
        "APPEND_COMPONENTS": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            }
        },
        "SECURITY": [{"BearerAuth": []}],
    }
    for key, value in overrides.items():
        if key == "APPEND_COMPONENTS" and isinstance(value, dict):
            components = dict(settings.get("APPEND_COMPONENTS", {}))
            for component_key, component_value in value.items():
                if isinstance(component_value, dict) and isinstance(
                    components.get(component_key), dict
                ):
                    merged = dict(components[component_key])
                    merged.update(component_value)
                    components[component_key] = merged
                else:
                    components[component_key] = component_value
            settings["APPEND_COMPONENTS"] = components
        else:
            settings[key] = value
    return settings