"""Django admin configuration for django-wee models."""

from django.contrib import admin

from .models import ShortUrl


@admin.register(ShortUrl)
class ShortUrlAdmin(admin.ModelAdmin[ShortUrl]):
    """Admin view for :class:`~django_wee.models.ShortUrl`.

    Displays the generated code and the original destination URL in the
    change list.
    """

    list_display = ("code", "url", "expires_at")
    search_fields = ("code__exact", "url")
    list_filter = ("expires_at",)
