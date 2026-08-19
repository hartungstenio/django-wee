# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add expiration support to short URLs through the `expires_at` field and database migration.
- Support optional expiration values in synchronous and asynchronous URL creation shortcuts.
- Add test coverage for expiration persistence and resolution.
- Prevent resolution of short URLs after their expiration time.

[unreleased]: https://github.com/hartungstenio/django-wee/releases
