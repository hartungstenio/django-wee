from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import BaseCache, caches
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils import timezone

if TYPE_CHECKING:
    from .models import ShortUrl

logger = logging.getLogger("django_wee")


def get_short_url_cache() -> BaseCache:
    return caches[getattr(settings, "WEE_CACHE_ALIAS", "default")]


def get_short_url_cache_timeout() -> float:
    return getattr(settings, "WEE_CACHE_TIMEOUT", 3600)


def get_short_url_cache_key(code: str) -> str:
    return f"{getattr(settings, 'WEE_CACHE_PREFIX', 'WEE')}:{code}"


def get_default_ttl() -> float | int | timedelta | None:
    """Return the value of ``WEE_DEFAULT_TTL`` from Django settings.

    Returns ``None`` when the setting is not defined, which means short URLs
    created without an explicit *expiration* or *ttl* will not expire.
    """
    return getattr(settings, "WEE_DEFAULT_TTL", None)


def redirect_to(url: str) -> HttpResponse:
    if getattr(settings, "WEE_PERMANENT_REDIRECT", True):
        logger.debug("Redirecting (permanent) to '%s'", url, extra={"url": url})
        return HttpResponsePermanentRedirect(url)
    logger.debug("Redirecting (temporary) to '%s'", url, extra={"url": url})
    return HttpResponseRedirect(url)


def cache_short_url(short_url: ShortUrl) -> None:
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


def normalize_url(url: str) -> str:
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
    return timezone.now() + delta
