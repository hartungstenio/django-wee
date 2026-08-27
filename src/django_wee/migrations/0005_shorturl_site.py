import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_wee", "0004_url_max_length_4096"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="shorturl",
            name="site",
            field=models.ForeignKey(
                db_comment="Foreign key to the site owning this URL",
                default=1,
                help_text="Site this URL belongs to",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="short_urls",
                to="sites.site",
                verbose_name="site",
            ),
            preserve_default=False,
        ),
    ]
