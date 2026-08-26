# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Cache errors are now suppressed instead of propagating to the caller. A cache failure no longer prevents URL creation or resolution.
- `WEE_CACHE_TIMEOUT` setting was being ignored — `get_short_url_cache_timeout()` was incorrectly reading `WEE_CACHE_ALIAS` instead.

### Added

- All significant operations now emit structured log records via the `django_wee` logger: URL creation (`INFO`), cache hits/misses/writes and redirects (`DEBUG`), and cache errors (`ERROR`). Enable with a standard Django `LOGGING` configuration targeting the `django_wee` logger.
- New `WEE_DEFAULT_TTL` setting: a project-wide default TTL (`int`/`float` seconds or `timedelta`) applied when `create_short_url` and `acreate_short_url` are called without an explicit `expiration` or `ttl`. When absent, the previous behaviour (no expiration) is preserved.

## [0.2.2] - 2026-08-24

### Added

- Searching and filtering in the admin interface
- pt-BR translations

## [0.2.1] - 2026-08-21

### Changed

- `ShortUrl.url` `max_length` increased from the Django `URLField` default (200) to 4096 to support long URLs such as S3 pre-signed URLs.

## [0.2.0] - 2026-08-20

### Added

- `create_short_url` and `acreate_short_url` now accept a `ttl` keyword argument (`int`, `float`, or `timedelta`) as an alternative to `expiration`. `expiration` and `ttl` are mutually exclusive and raise `ValueError` when both are given.
- `ShortUrlQuerySet.expired()` method that returns short URLs whose `expires_at` is set and in the past, complementing `alive()`.

### Changed

- **Breaking**: `expiration` is now a keyword-only argument of `create_short_url` and `acreate_short_url`. Calls that pass `expiration` positionally must be updated to use `expiration=...`. The new `ttl` keyword argument is also keyword-only.
- **Breaking**: removed the unique constraint on `ShortUrl.url`. The same destination URL may now be shortened multiple times, each with its own code and expiration. `create_short_url` and `acreate_short_url` no longer raise `ValidationError` for duplicate URLs.
- `create_short_url` and `acreate_short_url` now normalize URLs without a scheme to `https://` (e.g. `example.com` becomes `https://example.com`). Protocol-relative URLs receive an `https:` prefix, and URLs that already include a scheme are left unchanged.
- `delete_expired_short_urls` management command now uses the `ShortUrlQuerySet.expired()` method to select URLs for deletion.

## [0.1.0] - 2026-08-19

### Changed

- **Breaking**: `create_short_url` and `acreate_short_url` now return the persisted `ShortUrl` instance instead of the relative redirect path. Build the redirect path with `reverse("django_wee:redirect", args=[short_url.code])`.

### Added

- `ShortUrlQuerySet` custom queryset with an `alive()` method that filters out expired short URLs, used by `resolve_short_url` and `aresolve_short_url`.
- `resolve_short_url` and `aresolve_short_url` now populate the cache after a database lookup on a cache miss.
- `delete_expired_short_urls` management command that deletes expired short URLs, with an optional `--older-than` parameter to restrict deletion to URLs expired for at least the given duration and a `--dry-run` flag to preview the deletion.

## [0.0.1] - 2026-08-19

### Added

- Add expiration support to short URLs through the `expires_at` field and database migration.
- Support optional expiration values in synchronous and asynchronous URL creation shortcuts.
- Add test coverage for expiration persistence and resolution.
- Prevent resolution of short URLs after their expiration time.

[unreleased]: https://github.com/hartungstenio/django-wee/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/hartungstenio/django-wee/releases/tag/v0.2.0
[0.1.0]: https://github.com/hartungstenio/django-wee/releases/tag/v0.1.0
[0.0.1]: https://github.com/hartungstenio/django-wee/releases/tag/v0.0.1
