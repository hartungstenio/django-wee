from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("django_wee", "0002_url_expiration"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="shorturl",
            name="django_wee_shorturl_url_unq",
        ),
    ]
