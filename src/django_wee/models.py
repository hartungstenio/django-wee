"""Database models for django-wee."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_sqids import SqidsField
from django_stubs_ext.db.models import TypedModelMeta
from sqids.constants import DEFAULT_ALPHABET


class ShortUrl(models.Model):
    """Stores a mapping between a Sqids-based short code and its destination URL.

    The ``code`` is derived from the primary key via
    :class:`~django_sqids.SqidsField` and is used as the URL path segment
    for the redirect view. Minimum code length and alphabet can be
    customised via ``WEE_MIN_LEN`` and ``WEE_ALPHABET`` settings.
    """

    code = SqidsField(
        "id",
        _("Short url code"),
        min_length=getattr(settings, "WEE_MIN_LEN", 8),
        alphabet=getattr(settings, "WEE_ALPHABET", DEFAULT_ALPHABET),
        help_text=_("Short url code."),
    )
    url = models.URLField(
        _("original URL"),
        help_text=_("Complete URL"),
        db_comment="Complete URL",
    )

    class Meta(TypedModelMeta):
        """Metadata for :class:`ShortUrl`."""

        verbose_name = _("Short URL")
        verbose_name_plural = _("Short URLs")
        db_table_comment = "Short URLs"
        constraints = (
            models.UniqueConstraint(
                fields=("url",),
                name="%(app_label)s_%(class)s_url_unq",
                violation_error_code="unique",
                violation_error_message=_("URL already exists."),
            ),
        )

    def __str__(self) -> str:
        """Return the short code as the string representation."""
        return f"{self.code}: {self.url}"
