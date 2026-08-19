# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `create_short_url` and `acreate_short_url` now return the persisted `ShortUrl` instance instead of the relative redirect path. Build the redirect path with `reverse("django_wee:redirect", args=[short_url.code])`.

### Added

- `ShortUrlQuerySet` custom queryset with an `alive()` method that filters out expired short URLs, used by `resolve_short_url` and `aresolve_short_url`.
- `resolve_short_url` and `aresolve_short_url` now populate the cache after a database lookup on a cache miss.

## [0.0.1] - 2026-08-19

### Added

- Add expiration support to short URLs through the `expires_at` field and database migration.
- Support optional expiration values in synchronous and asynchronous URL creation shortcuts.
- Add test coverage for expiration persistence and resolution.
- Prevent resolution of short URLs after their expiration time.

[unreleased]: https://github.com/hartungstenio/django-wee/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/hartungstenio/django-wee/releases/tag/v0.0.1
