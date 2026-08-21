from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_wee", "0003_remove_url_unique_constraint"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shorturl",
            name="url",
            field=models.URLField(
                db_comment="Complete URL", help_text="Complete URL", max_length=4096, verbose_name="original URL"
            ),
        ),
    ]
