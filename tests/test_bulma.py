import pytest
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings

from djcrud.views.tables2 import Tables2Mixin


@pytest.mark.bulma
def test_tables2_mixin_uses_configured_frontend_settings():
    User = get_user_model()

    class UserTableView(Tables2Mixin):
        model = User
        model_meta = User._meta

    view = UserTableView()

    with override_settings(
        DJCRUD_FRONTEND="djcrud_bulma",
        DJCRUD_TABLES2_TEMPLATE="django_tables2/bulma.html",
        CRISPY_TEMPLATE_PACK="bulma",
        CRISPY_ALLOWED_TEMPLATE_PACKS=("bootstrap5", "bulma"),
    ):
        table_class = view.table_class

    assert table_class.Meta.template_name == "django_tables2/bulma.html"


@pytest.mark.bulma
def test_bulma_frontend_templates_exist():
    """Verify only djcrud-specific templates exist; crispy-bulma package provides all form templates."""
    package_dir = Path(__file__).resolve().parents[1] / "src" / "djcrud_bulma"

    for template in [
        "templates/djcrud/base.html",
        "templates/djcrud/list.html",
        "templates/djcrud/_actions_column.html",
        "templates/djcrud/confirm.html",
        "templates/djcrud/delete.html",
        "templates/django_tables2/bulma.html",
    ]:
        assert (package_dir / template).exists()

    # No custom bulma/ form templates (uses crispy-bulma package exclusively)
    assert not (package_dir / "templates/bulma").exists()
