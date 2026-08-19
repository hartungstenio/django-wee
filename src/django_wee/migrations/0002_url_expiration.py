from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_wee", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="shorturl",
            name="expires_at",
            field=models.DateTimeField(
                blank=True,
                db_comment="Expiration timestamp",
                help_text="When will this short url expire",
                null=True,
                verbose_name="expiration timestamp",
            ),
        ),
    ]
