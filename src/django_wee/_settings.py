"""Typed accessors for ``WEE_*`` keys in Django settings.

Each function reads one setting and returns a safe default, so the rest of
the codebase never has to call :func:`getattr` on the settings object directly.
"""

from datetime import timedelta

from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS, BaseCache, caches
from django.http.response import HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponseRedirectBase


def get_short_url_cache() -> BaseCache:
    """Return the Django cache backend configured for short-URL storage.

    Reads ``WEE_CACHE_ALIAS`` from Django settings.
    Falls back to the ``"default"`` cache when the setting is absent.
    """
    return caches[getattr(settings, "WEE_CACHE_ALIAS", DEFAULT_CACHE_ALIAS)]


def get_short_url_cache_timeout() -> float | None:
    """Return the cache entry lifetime in seconds.

    Reads ``WEE_CACHE_TIMEOUT`` from Django settings.
    Defaults to ``3600`` (one hour) when the setting is not defined.
    """
    return getattr(settings, "WEE_CACHE_TIMEOUT", 3600)


def get_short_url_cache_prefix() -> str:
    """Return the prefix used for short-URL cache keys.

    Reads ``WEE_CACHE_PREFIX`` from Django settings.
    Defaults to ``"WEE"`` when the setting is not defined.
    """
    prefix = getattr(settings, "WEE_CACHE_PREFIX", "WEE")
    if prefix is None:
        return ""
    return str(prefix)


def get_short_url_cache_key(code: str) -> str:
    """Build the cache key for a given short-URL *code*.

    Combines ``WEE_CACHE_PREFIX`` (default ``"WEE"``) with *code* using
    ``:`` as a separator, e.g. ``"WEE:abc123"``.
    """
    prefix = get_short_url_cache_prefix()
    if not prefix:
        return code
    return f"{prefix}:{code}"


def get_default_ttl() -> float | int | timedelta | None:
    """Return the value of ``WEE_DEFAULT_TTL`` from Django settings.

    Returns ``None`` when the setting is not defined, which means short URLs
    created without an explicit *expiration* or *ttl* will not expire.
    """
    return getattr(settings, "WEE_DEFAULT_TTL", None)


def get_redirect_response(url: str) -> HttpResponseRedirectBase:
    """Return an HTTP redirect response for *url*.

    Reads ``WEE_PERMANENT_REDIRECT`` from Django settings:

    * ``True`` (default) → :class:`~django.http.HttpResponsePermanentRedirect` (HTTP 301)
    * ``False`` → :class:`~django.http.HttpResponseRedirect` (HTTP 302)
    """
    if getattr(settings, "WEE_PERMANENT_REDIRECT", True):
        return HttpResponsePermanentRedirect(url)
    return HttpResponseRedirect(url)
