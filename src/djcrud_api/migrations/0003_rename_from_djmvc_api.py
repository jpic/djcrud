from django.db import connection, migrations


def rename_api_token_table(apps, schema_editor):
    """Upgrade databases that applied ``djmvc_api`` migrations."""
    tables = connection.introspection.table_names()
    if "djmvc_api_token" in tables and "djcrud_api_token" not in tables:
        schema_editor.execute(
            "ALTER TABLE djmvc_api_token RENAME TO djcrud_api_token",
        )


def rename_djmvc_api_migration_rows(apps, schema_editor):
    """Point ``django_migrations`` rows at the renamed app label."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE django_migrations SET app = 'djcrud_api' "
            "WHERE app = 'djmvc_api'",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("djcrud_api", "0002_rename_from_djmvc_swagger"),
    ]

    operations = [
        migrations.RunPython(
            rename_api_token_table,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            rename_djmvc_api_migration_rows,
            migrations.RunPython.noop,
        ),
    ]
