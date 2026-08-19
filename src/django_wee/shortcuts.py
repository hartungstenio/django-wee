"""Public shortcuts for creating short URLs.

Provides sync and async helpers that validate, persist, and cache a
:class:`~django_wee.models.ShortUrl` instance, returning the relative
redirect path ready to be included in a response.
"""

from datetime import datetime

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from ._internal import acache_short_url, cache_short_url, get_short_url_cache
from .models import ShortUrl


def create_short_url(url: str, expiration: datetime | None = None) -> str:
    """Create a short URL for the given URL and return its redirect path.

    Validates, persists, and caches the new ``ShortUrl`` instance, then
    returns the relative URL for the ``django_wee:redirect`` view.

    Args:
        url: The destination URL to shorten.

    Returns:
        The relative path (e.g. ``/s/abc123``) that redirects to *url*.

    Raises:
        ValidationError: If *url* fails model-level validation.
    """
    short_url = ShortUrl(url=url, expires_at=expiration)
    short_url.full_clean()
    short_url.save()
    cache_short_url(short_url)
    return reverse("django_wee:redirect", args=[short_url.code])


async def acreate_short_url(url: str, expiration: datetime | None = None) -> str:
    """Create a short URL for the given URL and return its redirect path.

    Async version of :func:`create_short_url`.

    Validates, persists, and caches the new ``ShortUrl`` instance
    asynchronously, then returns the relative URL for the
    ``django_wee:redirect`` view.

    Args:
        url: The destination URL to shorten.

    Returns:
        The relative path (e.g. ``/s/abc123``) that redirects to *url*.

    Raises:
        ValidationError: If *url* fails model-level validation.
    """
    short_url = ShortUrl(url=url, expires_at=expiration)
    await sync_to_async(short_url.full_clean)()
    await short_url.asave()
    await acache_short_url(short_url)
    return reverse("django_wee:redirect", args=[short_url.code])


def resolve_short_url(code: str) -> str:
    """Resolve *code* to its destination URL.

    Args:
        code: The short-URL code extracted from the request path.
    Raises:
        ObjectDoesNotExist: If no :class:`~django_wee.models.ShortUrl` matches *code*.
    """
    cache = get_short_url_cache()
    url: str = cache.get(code)
    if not url:
        short_url = ShortUrl.objects.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())).get(
            code=code
        )

        url = short_url.url
    return url


async def aresolve_short_url(code: str) -> str:
    """Resolve *code* to its destination URL.

    Async version of :func:`areverse_short_url`.

    Args:
        code: The short-URL code extracted from the request path.
    Raises:
        ObjectDoesNotExist: If no :class:`~django_wee.models.ShortUrl` matches *code*.
    """
    cache = get_short_url_cache()
    url: str = await cache.aget(code)
    if not url:
        short_url = await ShortUrl.objects.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())).aget(
            code=code
        )
        url = short_url.url
    return url
