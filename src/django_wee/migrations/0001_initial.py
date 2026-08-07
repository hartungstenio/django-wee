from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ShortUrl",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "url",
                    models.URLField(db_comment="Complete URL", help_text="Complete URL", verbose_name="original URL"),
                ),
            ],
            options={
                "verbose_name": "Short URL",
                "verbose_name_plural": "Short URLs",
                "db_table_comment": "Short URLs",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("url",),
                        name="django_wee_shorturl_url_unq",
                        violation_error_code="unique",
                        violation_error_message="URL already exists.",
                    ),
                ],
            },
        ),
    ]
