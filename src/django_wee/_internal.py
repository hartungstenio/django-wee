from __future__ import annotations

import logging
import warnings
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Final
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.contrib.sites.models import Site
from django.core.exceptions import SynchronousOnlyOperation
from django.urls import Resolver404, resolve
from django.utils import timezone

from ._settings import (
    get_default_ttl,
    get_redirect_response,
    get_short_url_cache,
    get_short_url_cache_key,
    get_short_url_cache_timeout,
)

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

    from .models import ShortUrl

logger = logging.getLogger("django_wee")


def redirect_to(url: str) -> HttpResponse:
    """Build and return an HTTP redirect response to *url*, logging the outcome."""
    response = get_redirect_response(url)
    logger.debug("Redirecting to '%s'", url, extra={"url": url, "status_code": response.status_code})
    return response


def cache_short_url(short_url: ShortUrl) -> None:
    """Store *short_url*'s destination in the cache.

    The timeout is the greater of ``WEE_CACHE_TIMEOUT`` and the remaining
    time until ``short_url.expires_at``, so the entry never expires before
    the short URL itself does. Cache errors are suppressed and logged.
    """
    cache = get_short_url_cache()
    timeout = get_short_url_cache_timeout()

    if short_url.expires_at:
        expiration = short_url.expires_at - timezone.now()
        timeout = max(timeout, expiration.total_seconds())

    cache_key = get_short_url_cache_key(short_url.code)
    try:
        cache.set(cache_key, short_url.url, timeout=timeout)
        logger.debug("Cached short code '%s'", short_url.code, extra={"code": short_url.code, "timeout": timeout})
    except Exception:
        logger.exception("Could not cache URL for short code '%s'", short_url.code, extra={"cache_key": cache_key})


async def acache_short_url(short_url: ShortUrl) -> None:
    """Async variant of :func:`cache_short_url`."""
    cache = get_short_url_cache()
    timeout = get_short_url_cache_timeout()

    if short_url.expires_at:
        expiration = short_url.expires_at - timezone.now()
        timeout = max(timeout, expiration.total_seconds())

    cache_key = get_short_url_cache_key(short_url.code)
    try:
        await cache.aset(cache_key, short_url.url, timeout=timeout)
        logger.debug("Cached short code '%s'", short_url.code, extra={"code": short_url.code, "timeout": timeout})
    except Exception:
        logger.exception("Could not cache URL for short code '%s'", short_url.code, extra={"cache_key": cache_key})


def get_cached_short_code(code: str) -> str | None:
    """Return the cached destination URL for *code*, or ``None`` on miss or error.

    Cache errors are suppressed and logged; callers should fall back to a
    database lookup when ``None`` is returned.
    """
    cache = get_short_url_cache()
    cache_key = get_short_url_cache_key(code)

    try:
        result: str | None = cache.get(cache_key)
    except Exception:
        logger.exception("Could not read short code '%s' from cache", code, extra={"cache_key": cache_key})
        return None

    if result is None:
        logger.debug("Cache miss for short code '%s'", code, extra={"code": code})
    else:
        logger.debug("Cache hit for short code '%s'", code, extra={"code": code})
    return result


async def aget_cached_short_code(code: str) -> str | None:
    """Async variant of :func:`get_cached_short_code`."""
    cache = get_short_url_cache()
    cache_key = get_short_url_cache_key(code)

    try:
        result: str | None = await cache.aget(cache_key)
    except Exception:
        logger.exception("Could not read short code '%s' from cache", code, extra={"cache_key": cache_key})
        return None

    if result is None:
        logger.debug("Cache miss for short code '%s'", code, extra={"code": code})
    else:
        logger.debug("Cache hit for short code '%s'", code, extra={"code": code})
    return result


def normalize_url(url: str, site: Site) -> str:
    """Normalize *url* to an absolute URL.

    Absolute URLs are returned unchanged. Protocol-relative URLs such as
    ``"//example.com"`` receive the ``https:`` prefix. Schemeless hostnames such
    as ``"example.com"`` become ``"https://example.com"``. Relative URLs such as
    ``"/about/"`` are resolved against the current site domain when *site* is
    provided.

    Args:
        url: The URL to normalize.
        site: Optional :class:`~django.contrib.sites.models.Site` instance used to
            resolve relative URLs.

    Returns:
        The normalized absolute URL.
    """
    parsed = urlparse(url)
    if parsed.scheme:
        return url

    if url.startswith("//"):
        return f"https:{url}"

    if url.startswith("/"):
        try:
            resolve(url)
        except Resolver404 as exc:
            msg = "Relative URLs must belong to the current site"
            raise ValueError(msg) from exc
        else:
            url = f"{site.domain}{url}"

    return f"https://{url}"


def resolve_expiration(
    expiration: datetime | None,
    ttl: int | float | timedelta | None,
) -> datetime | None:
    """Resolve an expiration datetime from *expiration* or *ttl*.

    Exactly one of *expiration* or *ttl* may be given. *ttl* is interpreted
    as a duration from now: an :class:`int` or :class:`float` is treated as
    a number of seconds and a :class:`~datetime.timedelta` is used directly.

    When neither argument is provided, the value of the ``WEE_DEFAULT_TTL``
    Django setting is used as the *ttl* fallback. If that setting is also absent,
    the function returns ``None``, meaning the short URL will not expire.
    """
    if expiration is not None and ttl is not None:
        msg = "expiration and ttl are mutually exclusive"
        raise ValueError(msg)

    if expiration is None and ttl is None:
        ttl = get_default_ttl()

    if ttl is None:
        return expiration

    delta = ttl if isinstance(ttl, timedelta) else timedelta(seconds=ttl)

    _zero: Final[timedelta] = timedelta(0)
    if delta < _zero:
        msg = "ttl must be a positive duration"
        raise ValueError(msg)

    if delta == _zero:
        warnings.warn(
            "ttl is zero — the short URL will expire immediately",
            UserWarning,
            stacklevel=3,
        )

    return timezone.now() + delta


def get_current_site(request: HttpRequest | None = None) -> Site:
    """Get the current site."""
    return Site.objects.get_current(request)


async def aget_current_site(request: HttpRequest | None = None) -> Site:
    """Get the current site.

    Async version of :func:`get_current_site`.

    Tries to take advantage of the site's cache before switching context.
    """
    try:
        return Site.objects.get_current(request)
    except SynchronousOnlyOperation:
        return await sync_to_async(Site.objects.get_current)()
