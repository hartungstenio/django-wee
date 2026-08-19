from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import BaseCache, caches
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils import timezone

if TYPE_CHECKING:
    from .models import ShortUrl


def get_short_url_cache() -> BaseCache:
    return caches[getattr(settings, "WEE_CACHE_ALIAS", "default")]


def get_short_url_cache_timeout() -> float:
    return getattr(settings, "WEE_CACHE_ALIAS", 3600)


def redirect_to(url: str) -> HttpResponse:
    if getattr(settings, "WEE_PERMANENT_REDIRECT", True):
        return HttpResponsePermanentRedirect(url)
    return HttpResponseRedirect(url)


def cache_short_url(short_url: ShortUrl) -> None:
    cache = get_short_url_cache()
    timeout = get_short_url_cache_timeout()

    if short_url.expires_at:
        expiration = short_url.expires_at - timezone.now()
        timeout = max(timeout, expiration.total_seconds())

    cache.set(short_url.code, short_url.url, timeout=get_short_url_cache_timeout())


async def acache_short_url(short_url: ShortUrl) -> None:
    cache = get_short_url_cache()
    timeout = get_short_url_cache_timeout()

    if short_url.expires_at:
        expiration = short_url.expires_at - timezone.now()
        timeout = max(timeout, expiration.total_seconds())

    await cache.aset(short_url.code, short_url.url, timeout=get_short_url_cache_timeout())
