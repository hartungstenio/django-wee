# django-wee

[![PyPI - Version](https://img.shields.io/pypi/v/django-wee.svg)](https://pypi.org/project/django-wee)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-wee.svg)](https://pypi.org/project/django-wee)

A minimal Django application for creating and resolving short URLs, backed by [Sqids](https://sqids.org/) codes and Django's cache framework.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Settings reference](#settings-reference)
- [License](#license)

## Requirements

- Python 3.10+
- Django 5.2+

## Installation

```console
pip install django-wee
```

Add `django_wee` to `INSTALLED_APPS` and include its URL patterns:

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django_wee",
]
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path("s/", include("django_wee.urls")),
]
```

Then run the migrations:

```console
python manage.py migrate
```

### ASGI / async projects

If your project runs under an ASGI server, use the async URL module instead:

```python
(path("s/", include("django_wee.urls_async")),)
```

## Configuration

No mandatory configuration is required. See [Settings reference](#settings-reference) for optional tunables.

## Usage

### Creating short URLs

Use the provided shortcut functions anywhere in your code:

```python
from django.urls import reverse
from django_wee.shortcuts import create_short_url

short_url = create_short_url("https://example.com/a/very/long/url")
short_path = reverse("django_wee:redirect", args=[short_url.code])
# → "/s/aBcD1234/"
```

Pass an optional timezone-aware expiration datetime to create a URL that stops
resolving after the specified time:

```python
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from django_wee.shortcuts import create_short_url

expiration = timezone.now() + timedelta(days=7)
short_url = create_short_url("https://example.com/a/very/long/url", expiration)
short_path = reverse("django_wee:redirect", args=[short_url.code])
```

If no expiration is provided, the short URL does not expire.

An async variant is also available:

```python
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from django_wee.shortcuts import acreate_short_url

expiration = timezone.now() + timedelta(days=7)
short_url = await acreate_short_url("https://example.com/a/very/long/url", expiration)
short_path = reverse("django_wee:redirect", args=[short_url.code])
```

Both functions validate the URL, persist a `ShortUrl` record, populate the cache, and return the persisted `ShortUrl` instance.

### Resolving short URLs

Requests to `GET /s/<code>/` are handled automatically by the redirect view. The view checks the cache first and falls back to the database. Expired short URLs are not resolved. The response type (301 or 302) is controlled by the `WEE_PERMANENT_REDIRECT` setting.

### Deleting expired URLs

The `delete_expired_short_urls` management command removes expired short URLs from the database:

```console
python manage.py delete_expired_short_urls
```

By default, every short URL whose `expires_at` timestamp is in the past is deleted. Use `--older-than` to restrict the deletion to URLs that have been expired for at least the given duration:

```console
python manage.py delete_expired_short_urls --older-than "7 days"
```

The duration accepts any format supported by Django's `parse_duration` (e.g. `"7 days"`, `"12 hours"`, `"PT30M"`).

Use `--dry-run` to preview how many URLs would be deleted without performing the deletion:

```console
python manage.py delete_expired_short_urls --older-than "7 days" --dry-run
```

## Settings reference

| Setting | Default | Description |
| --- | --- | --- |
| `WEE_CACHE_ALIAS` | `"default"` | Cache alias (from `CACHES`) used to store short-URL mappings. |
| `WEE_CACHE_TIMEOUT` | `3600` | Cache TTL in seconds. |
| `WEE_CACHE_PREFIX` | `"WEE"` | Prefix used for short-URL cache keys. Keys use the `prefix:code` format. |
| `WEE_MIN_LEN` | `8` | Minimum length of the generated Sqids code. |
| `WEE_ALPHABET` | Sqids default | Character set used to generate codes. |
| `WEE_PERMANENT_REDIRECT` | `True` | If `True`, the redirect view returns HTTP 301; otherwise HTTP 302. |

## License

`django-wee` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
