"""Public shortcuts for creating short URLs.

Provides sync and async helpers that validate, persist, and cache a
:class:`~django_wee.models.ShortUrl` instance, returning the relative
redirect path ready to be included in a response.
"""

from asgiref.sync import sync_to_async
from django.urls import reverse

from ._internal import acache_short_url, cache_short_url
from .models import ShortUrl


def create_short_url(url: str) -> str:
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
    short_url = ShortUrl(url=url)
    short_url.full_clean()
    short_url.save()
    cache_short_url(short_url)
    return reverse("django_wee:redirect", args=[short_url.code])


async def acreate_short_url(url: str) -> str:
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
    short_url = ShortUrl(url=url)
    await sync_to_async(short_url.full_clean)()
    await short_url.asave()
    await acache_short_url(short_url)
    return reverse("django_wee:redirect", args=[short_url.code])
