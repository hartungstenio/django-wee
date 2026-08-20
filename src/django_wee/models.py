"""Database models for django-wee."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_sqids import SqidsField
from django_stubs_ext.db.models import TypedModelMeta
from sqids.constants import DEFAULT_ALPHABET

from ._compat import Self, override


class ShortUrlQuerySet(models.QuerySet["ShortUrl"]):
    """Custom queryset for :class:`ShortUrl` with expiration-aware helpers."""

    def alive(self) -> Self:
        """Return short URLs that have not expired.

        Includes records with no expiration (``expires_at`` is ``None``)
        and records whose expiration is in the future.
        """
        return self.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))

    def expired(self) -> Self:
        """Return short URLs that have expired.

        Includes only records whose expiration is set and in the past.
        Records with no expiration (``expires_at`` is ``None``) are
        excluded.
        """
        return self.filter(expires_at__isnull=False, expires_at__lte=timezone.now())


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
    expires_at = models.DateTimeField(
        _("expiration timestamp"),
        blank=True,
        null=True,
        help_text=_("When will this short url expire"),
        db_comment="Expiration timestamp",
    )

    objects = ShortUrlQuerySet.as_manager()

    class Meta(TypedModelMeta):
        """Metadata for :class:`ShortUrl`."""

        verbose_name = _("Short URL")
        verbose_name_plural = _("Short URLs")
        db_table_comment = "Short URLs"

    @override
    def __str__(self) -> str:
        """Return the short code as the string representation."""
        return f"{self.code}: {self.url}"
