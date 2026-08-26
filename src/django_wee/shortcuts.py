"""Public shortcuts for creating short URLs.

Provides sync and async helpers that validate, persist, and cache a
:class:`~django_wee.models.ShortUrl` instance, returning the relative
redirect path ready to be included in a response.
"""

import logging
from datetime import datetime, timedelta
from typing import overload
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.utils import timezone

from ._internal import acache_short_url, aget_cached_short_code, cache_short_url, get_cached_short_code
from .models import ShortUrl

logger = logging.getLogger("django_wee")


def _normalize_url(url: str) -> str:
    """Prepend ``https://`` when *url* has no scheme.

    A schemeless URL such as ``"example.com"`` becomes
    ``"https://example.com"``. Protocol-relative URLs (``"//example.com"``)
    receive only the ``https:`` prefix. URLs that already include a scheme
    are returned unchanged.
    """
    if urlparse(url).scheme:
        return url
    if url.startswith("//"):
        return f"https:{url}"
    return f"https://{url}"


def _resolve_expiration(
    expiration: datetime | None,
    ttl: int | float | timedelta | None,
) -> datetime | None:
    """Resolve an expiration datetime from *expiration* or *ttl*.

    Exactly one of *expiration* or *ttl* may be given. *ttl* is interpreted
    as a duration from now: an :class:`int` or :class:`float` is treated as
    a number of seconds and a :class:`~datetime.timedelta` is used directly.
    """
    if expiration is not None and ttl is not None:
        msg = "expiration and ttl are mutually exclusive"
        raise ValueError(msg)
    if ttl is None:
        return expiration
    delta = ttl if isinstance(ttl, timedelta) else timedelta(seconds=ttl)
    return timezone.now() + delta


@overload
def create_short_url(url: str) -> ShortUrl:
    """Create a short URL that never expires."""


@overload
def create_short_url(url: str, *, expiration: datetime) -> ShortUrl:
    """Create a short URL that expires at *expiration*."""


@overload
def create_short_url(url: str, *, ttl: int | float | timedelta) -> ShortUrl:
    """Create a short URL that expires after *ttl* from now."""


def create_short_url(
    url: str,
    *,
    expiration: datetime | None = None,
    ttl: int | float | timedelta | None = None,
) -> ShortUrl:
    """Create a short URL for the given URL and return the persisted instance.

    Validates, persists, and caches the new ``ShortUrl`` instance, then
    returns it. Build the redirect path with
    :func:`~django.urls.reverse` and the ``django_wee:redirect`` view
    using ``short_url.code``.

    Args:
        url: The destination URL to shorten.
        expiration: Optional timezone-aware datetime at which the short
            URL stops resolving. Mutually exclusive with *ttl*.
        ttl: Optional time-to-live duration from now. An :class:`int` or
            :class:`float` is interpreted as seconds, and a
            :class:`~datetime.timedelta` is used directly. Mutually
            exclusive with *expiration*.

    Returns:
        The persisted :class:`~django_wee.models.ShortUrl` instance.

    Raises:
        ValidationError: If *url* fails model-level validation.
        ValueError: If both *expiration* and *ttl* are given.
    """
    short_url = ShortUrl(
        url=_normalize_url(url),
        expires_at=_resolve_expiration(expiration, ttl),
    )
    short_url.full_clean()
    short_url.save()
    logger.info(
        "Short URL '%s' created for '%s'",
        short_url.code,
        short_url.url,
        extra={"code": short_url.code, "url": short_url.url, "expires_at": short_url.expires_at},
    )
    cache_short_url(short_url)
    return short_url


@overload
async def acreate_short_url(url: str) -> ShortUrl:
    """Create a short URL that never expires."""


@overload
async def acreate_short_url(url: str, *, expiration: datetime) -> ShortUrl:
    """Create a short URL that expires at *expiration*."""


@overload
async def acreate_short_url(url: str, *, ttl: int | float | timedelta) -> ShortUrl:
    """Create a short URL that expires after *ttl* from now."""


async def acreate_short_url(
    url: str,
    *,
    expiration: datetime | None = None,
    ttl: int | float | timedelta | None = None,
) -> ShortUrl:
    """Create a short URL for the given URL and return the persisted instance.

    Async version of :func:`create_short_url`.

    Validates, persists, and caches the new ``ShortUrl`` instance
    asynchronously, then returns it. Build the redirect path with
    :func:`~django.urls.reverse` and the ``django_wee:redirect`` view
    using ``short_url.code``.

    Args:
        url: The destination URL to shorten.
        expiration: Optional timezone-aware datetime at which the short
            URL stops resolving. Mutually exclusive with *ttl*.
        ttl: Optional time-to-live duration from now. An :class:`int` or
            :class:`float` is interpreted as seconds, and a
            :class:`~datetime.timedelta` is used directly. Mutually
            exclusive with *expiration*.

    Returns:
        The persisted :class:`~django_wee.models.ShortUrl` instance.

    Raises:
        ValidationError: If *url* fails model-level validation.
        ValueError: If both *expiration* and *ttl* are given.
    """
    short_url = ShortUrl(
        url=_normalize_url(url),
        expires_at=_resolve_expiration(expiration, ttl),
    )
    await sync_to_async(short_url.full_clean)()
    await short_url.asave()
    logger.info(
        "Short URL '%s' created for '%s'",
        short_url.code,
        short_url.url,
        extra={"code": short_url.code, "url": short_url.url, "expires_at": short_url.expires_at},
    )
    await acache_short_url(short_url)
    return short_url


def resolve_short_url(code: str) -> str:
    """Resolve *code* to its destination URL.

    Args:
        code: The short-URL code extracted from the request path.
    Raises:
        ObjectDoesNotExist: If no :class:`~django_wee.models.ShortUrl` matches *code*.
    """
    url: str | None = get_cached_short_code(code)
    if not url:
        logger.debug("Fetching short code '%s' from database", code, extra={"code": code})
        short_url = ShortUrl.objects.alive().get(code=code)  # pyrefly: ignore [missing-attribute]
        cache_short_url(short_url)
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
    url: str | None = await aget_cached_short_code(code)
    if not url:
        logger.debug("Fetching short code '%s' from database", code, extra={"code": code})
        short_url = await ShortUrl.objects.alive().aget(code=code)  # pyrefly: ignore [missing-attribute]
        await acache_short_url(short_url)
        url = short_url.url
    return url
