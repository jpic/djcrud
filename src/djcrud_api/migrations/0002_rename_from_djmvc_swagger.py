from django.db import connection, migrations


def rename_swagger_token_table(apps, schema_editor):
    """Upgrade databases that applied ``djmvc_swagger`` migrations."""
    tables = connection.introspection.table_names()
    if "djmvc_swagger_token" in tables and "djmvc_api_token" not in tables:
        schema_editor.execute(
            "ALTER TABLE djmvc_swagger_token RENAME TO djmvc_api_token",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("djcrud_api", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            rename_swagger_token_table,
            migrations.RunPython.noop,
        ),
    ]
