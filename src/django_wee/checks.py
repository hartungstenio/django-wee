"""System checks for django-wee cache configuration.

These checks validate the cache backend and TTL settings used by the short-url
lookup layer so misconfiguration is surfaced early during Django startup.
"""

from collections.abc import Iterable, Sequence
from typing import Any

from django.apps.config import AppConfig
from django.core import checks
from django.core.cache import InvalidCacheBackendError
from django.core.cache.backends.db import DatabaseCache

from ._settings import get_short_url_cache, get_short_url_cache_prefix, get_short_url_cache_timeout

# Errors
E001 = checks.Error(
    "WEE_CACHE_ALIAS points to an invalid cache backend. The configured cache alias "
    "does not exist in CACHES, so django-wee cannot store short-URL lookups in "
    "cache and will fall back to database lookups instead. Set WEE_CACHE_ALIAS to "
    "a valid cache name such as 'default' or another backend that is configured in "
    "CACHES.",
    id="django_wee.E001",
)
# Warnings
W001 = checks.Warning(
    "WEE_CACHE_ALIAS points to a database cache. Because cache misses still require "
    "reading from the database, a database-backed cache does not provide a "
    "meaningful performance benefit for short-URL lookups and can increase load on "
    "your primary database. Prefer a dedicated cache backend such as Redis or "
    "Memcached for short-link lookups.",
    id="django_wee.W001",
)
W002 = checks.Warning(
    "WEE_CACHE_TIMEOUT is not set to a positive number of seconds, which disables "
    "or weakens the cache TTL for short-URL entries and can allow stale mappings to "
    "linger for too long. Set WEE_CACHE_TIMEOUT to a positive value so redirect "
    "lookups expire predictably and the cache does not accumulate stale data.",
    id="django_wee.W002",
)
W003 = checks.Warning(
    "WEE_CACHE_PREFIX is empty. Empty cache prefixes can cause cache-key collisions "
    "and make short-URL lookups harder to reason about or debug. Set "
    "WEE_CACHE_PREFIX to a non-empty value such as 'WEE'.",
    id="django_wee.W003",
)


@checks.register(checks.Tags.caches)
def check_cache(
    *,
    app_configs: Sequence[AppConfig] | None,  # noqa: ARG001
    databases: Sequence[str] | None = None,  # noqa: ARG001
    **kwargs: Any,  # noqa: ANN401, ARG001
) -> Iterable[checks.CheckMessage]:
    """Validate the cache backend and TTL used for short-URL lookups.

    Returns Django check messages when the configured cache alias is invalid,
    when the chosen backend is a database cache, or when the TTL is disabled by
    setting it to ``None``.
    """
    try:
        cache = get_short_url_cache()
    except InvalidCacheBackendError:
        yield E001
    else:
        if isinstance(cache, DatabaseCache):
            yield W001
        timeout = get_short_url_cache_timeout()
        if timeout is None or timeout <= 0:
            yield W002

        prefix = get_short_url_cache_prefix()
        if not prefix:
            yield W003
