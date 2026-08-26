from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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
