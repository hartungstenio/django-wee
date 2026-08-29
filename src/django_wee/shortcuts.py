"""Public shortcuts for creating short URLs.

Provides sync and async helpers that validate, persist, and cache a
:class:`~django_wee.models.ShortUrl` instance, returning the relative
redirect path ready to be included in a response.
"""

import logging
from datetime import datetime, timedelta
from typing import overload

from asgiref.sync import sync_to_async
from django.contrib.sites.models import Site

from django_wee._internal import aget_current_site, get_current_site

from ._internal import (
    acache_short_url,
    aget_cached_short_code,
    cache_short_url,
    get_cached_short_code,
    normalize_url,
    resolve_expiration,
)
from .models import ShortUrl

logger = logging.getLogger("django_wee")


@overload
def create_short_url(url: str, *, site: Site | None = None) -> ShortUrl:
    """Create a short URL using the ``WEE_DEFAULT_TTL`` setting, or no expiration if unset.

    Args:
        url: The destination URL to shorten.
        site: Optional :class:`~django.contrib.sites.models.Site` instance. If not
            provided, the current site is used.
    """


@overload
def create_short_url(url: str, *, expiration: datetime, site: Site | None = None) -> ShortUrl:
    """Create a short URL that expires at *expiration*.

    Args:
        url: The destination URL to shorten.
        expiration: Timezone-aware datetime at which the short URL stops resolving.
        site: Optional :class:`~django.contrib.sites.models.Site` instance. If not
            provided, the current site is used.
    """


@overload
def create_short_url(url: str, *, ttl: int | float | timedelta, site: Site | None = None) -> ShortUrl:
    """Create a short URL that expires after *ttl* from now.

    Args:
        url: The destination URL to shorten.
        ttl: Time-to-live duration from now. An :class:`int` or :class:`float` is
            interpreted as seconds, and a :class:`~datetime.timedelta` is used
            directly.
        site: Optional :class:`~django.contrib.sites.models.Site` instance. If not
            provided, the current site is used.
    """


def create_short_url(
    url: str,
    *,
    expiration: datetime | None = None,
    ttl: int | float | timedelta | None = None,
    site: Site | None = None,
) -> ShortUrl:
    """Create a short URL for the given URL and return the persisted instance.

    Validates, persists, and caches the new ``ShortUrl`` instance, then
    returns it. Build the redirect path with
    :func:`~django.urls.reverse` and the ``django_wee:redirect`` view
    using ``short_url.code``.

    When neither *expiration* nor *ttl* is given, the ``WEE_DEFAULT_TTL``
    Django setting is used as the TTL fallback. If that setting is also absent,
    the short URL will not expire.

    Args:
        url: The destination URL to shorten.
        expiration: Optional timezone-aware datetime at which the short
            URL stops resolving. Mutually exclusive with *ttl*.
        ttl: Optional time-to-live duration from now. An :class:`int` or
            :class:`float` is interpreted as seconds, and a
            :class:`~datetime.timedelta` is used directly. Mutually
            exclusive with *expiration*.
        site: Optional :class:`~django.contrib.sites.models.Site` instance.
            If not provided, the current site is used.

    Returns:
        The persisted :class:`~django_wee.models.ShortUrl` instance.

    Raises:
        ValidationError: If *url* fails model-level validation.
        ValueError: If both *expiration* and *ttl* are given.
    """
    if site is None:
        site = get_current_site()
    short_url = ShortUrl(
        url=normalize_url(url, site=site),
        expires_at=resolve_expiration(expiration, ttl),
        site=site,
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
async def acreate_short_url(url: str, *, site: Site | None = None) -> ShortUrl:
    """Create a short URL using the ``WEE_DEFAULT_TTL`` setting, or no expiration if unset.

    Args:
        url: The destination URL to shorten.
        site: Optional :class:`~django.contrib.sites.models.Site` instance. If not
            provided, the current site is used.
    """


@overload
async def acreate_short_url(url: str, *, expiration: datetime, site: Site | None = None) -> ShortUrl:
    """Create a short URL that expires at *expiration*.

    Args:
        url: The destination URL to shorten.
        expiration: Timezone-aware datetime at which the short URL stops resolving.
        site: Optional :class:`~django.contrib.sites.models.Site` instance. If not
            provided, the current site is used.
    """


@overload
async def acreate_short_url(url: str, *, ttl: int | float | timedelta, site: Site | None = None) -> ShortUrl:
    """Create a short URL that expires after *ttl* from now.

    Args:
        url: The destination URL to shorten.
        ttl: Time-to-live duration from now. An :class:`int` or :class:`float` is
            interpreted as seconds, and a :class:`~datetime.timedelta` is used
            directly.
        site: Optional :class:`~django.contrib.sites.models.Site` instance. If not
            provided, the current site is used.
    """


async def acreate_short_url(
    url: str,
    *,
    expiration: datetime | None = None,
    ttl: int | float | timedelta | None = None,
    site: Site | None = None,
) -> ShortUrl:
    """Create a short URL for the given URL and return the persisted instance.

    Async version of :func:`create_short_url`.

    Validates, persists, and caches the new ``ShortUrl`` instance
    asynchronously, then returns it. Build the redirect path with
    :func:`~django.urls.reverse` and the ``django_wee:redirect`` view
    using ``short_url.code``.

    When neither *expiration* nor *ttl* is given, the ``WEE_DEFAULT_TTL``
    Django setting is used as the TTL fallback. If that setting is also absent,
    the short URL will not expire.

    Args:
        url: The destination URL to shorten.
        expiration: Optional timezone-aware datetime at which the short
            URL stops resolving. Mutually exclusive with *ttl*.
        ttl: Optional time-to-live duration from now. An :class:`int` or
            :class:`float` is interpreted as seconds, and a
            :class:`~datetime.timedelta` is used directly. Mutually
            exclusive with *expiration*.
        site: Optional :class:`~django.contrib.sites.models.Site` instance.
            If not provided, the current site is used.

    Returns:
        The persisted :class:`~django_wee.models.ShortUrl` instance.

    Raises:
        ValidationError: If *url* fails model-level validation.
        ValueError: If both *expiration* and *ttl* are given.
    """
    if site is None:
        site = await aget_current_site()
    short_url = ShortUrl(
        url=normalize_url(url, site=site),
        site=site,
        expires_at=resolve_expiration(expiration, ttl),
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


def resolve_short_url(code: str, site: Site) -> str:
    """Resolve *code* to its destination URL.

    Args:
        code: The short-URL code extracted from the request path.
        site: The :class:`~django.contrib.sites.models.Site` whose short URLs are
            being resolved.

    Returns:
        The destination URL associated with *code* for *site*.

    Raises:
        ObjectDoesNotExist: If no :class:`~django_wee.models.ShortUrl` matches
            *code* for *site*.
    """
    url: str | None = get_cached_short_code(code)
    if not url:
        logger.debug("Fetching short code '%s' from database", code, extra={"code": code})
        short_url = ShortUrl.objects.alive().get(code=code, site=site)  # pyrefly: ignore [missing-attribute]
        cache_short_url(short_url)
        url = short_url.url
    return url


async def aresolve_short_url(code: str, site: Site) -> str:
    """Resolve *code* to its destination URL.

    Async version of :func:`resolve_short_url`.

    Args:
        code: The short-URL code extracted from the request path.
        site: The :class:`~django.contrib.sites.models.Site` whose short URLs are
            being resolved.

    Returns:
        The destination URL associated with *code* for *site*.

    Raises:
        ObjectDoesNotExist: If no :class:`~django_wee.models.ShortUrl` matches
            *code* for *site*.
    """
    url: str | None = await aget_cached_short_code(code)
    if not url:
        logger.debug("Fetching short code '%s' from database", code, extra={"code": code})
        short_url = await ShortUrl.objects.alive().aget(code=code, site=site)  # pyrefly: ignore [missing-attribute]
        await acache_short_url(short_url)
        url = short_url.url
    return url
