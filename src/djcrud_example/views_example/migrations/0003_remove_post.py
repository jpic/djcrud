from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("views_example", "0002_article_owner"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Post",
        ),
    ]
