from datetime import timedelta

import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.test import override_settings
from django.utils import timezone

from django_wee._internal import get_short_url_cache
from django_wee.models import ShortUrl
from django_wee.shortcuts import acreate_short_url, aresolve_short_url, create_short_url, resolve_short_url

from .factories import ShortUrlFactory


@pytest.mark.django_db
class TestCreateShortUrl:
    def test_returns_persisted_short_url(self) -> None:
        short_url = create_short_url("https://example.com")
        persisted = ShortUrl.objects.get(url="https://example.com")
        assert short_url == persisted

    def test_persists_to_db_and_populates_cache(self) -> None:
        create_short_url("https://example.com")
        short_url = ShortUrl.objects.get(url="https://example.com")
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == "https://example.com"

    def test_persists_expiration(self) -> None:
        expiration = timezone.now() + timedelta(days=1)

        create_short_url("https://example.com", expiration=expiration)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at == expiration

    def test_persists_ttl_as_int_seconds(self) -> None:
        before = timezone.now()

        create_short_url("https://example.com", ttl=3600)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=3600) <= short_url.expires_at <= timezone.now() + timedelta(seconds=3600)

    def test_persists_ttl_as_float_seconds(self) -> None:
        before = timezone.now()

        create_short_url("https://example.com", ttl=1.5)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=1.5) <= short_url.expires_at <= timezone.now() + timedelta(seconds=1.5)

    def test_persists_ttl_as_timedelta(self) -> None:
        before = timezone.now()
        delta = timedelta(hours=2)

        create_short_url("https://example.com", ttl=delta)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + delta <= short_url.expires_at <= timezone.now() + delta

    def test_expiration_and_ttl_are_mutually_exclusive(self) -> None:
        expiration = timezone.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="mutually exclusive"):
            create_short_url("https://example.com", expiration=expiration, ttl=3600)  # type: ignore[call-overload]

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            create_short_url("not-a-url")

    def test_duplicate_url_raises(self) -> None:
        existing = ShortUrlFactory.create()
        with pytest.raises(ValidationError):
            create_short_url(existing.url)


@pytest.mark.django_db
class TestACreateShortUrl:
    def test_returns_persisted_short_url(self) -> None:
        short_url = async_to_sync(acreate_short_url)("https://example.com")
        persisted = ShortUrl.objects.get(url="https://example.com")
        assert short_url == persisted

    def test_persists_to_db_and_populates_cache(self) -> None:
        async_to_sync(acreate_short_url)("https://example.com")
        short_url = ShortUrl.objects.get(url="https://example.com")
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == "https://example.com"

    def test_persists_expiration(self) -> None:
        expiration = timezone.now() + timedelta(days=1)

        async_to_sync(acreate_short_url)("https://example.com", expiration=expiration)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at == expiration

    def test_persists_ttl_as_int_seconds(self) -> None:
        before = timezone.now()

        async_to_sync(acreate_short_url)("https://example.com", ttl=3600)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=3600) <= short_url.expires_at <= timezone.now() + timedelta(seconds=3600)

    def test_persists_ttl_as_float_seconds(self) -> None:
        before = timezone.now()

        async_to_sync(acreate_short_url)("https://example.com", ttl=1.5)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=1.5) <= short_url.expires_at <= timezone.now() + timedelta(seconds=1.5)

    def test_persists_ttl_as_timedelta(self) -> None:
        before = timezone.now()
        delta = timedelta(hours=2)

        async_to_sync(acreate_short_url)("https://example.com", ttl=delta)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + delta <= short_url.expires_at <= timezone.now() + delta

    def test_expiration_and_ttl_are_mutually_exclusive(self) -> None:
        expiration = timezone.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="mutually exclusive"):
            async_to_sync(acreate_short_url)("https://example.com", expiration=expiration, ttl=3600)

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            async_to_sync(acreate_short_url)("not-a-url")

    def test_duplicate_url_raises(self) -> None:
        existing = ShortUrlFactory.create()
        with pytest.raises(ValidationError):
            async_to_sync(acreate_short_url)(existing.url)


@pytest.mark.django_db
class TestResolveShortUrl:
    def test_returns_url_from_cache(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"WEE:{short_url.code}", short_url.url)

        assert resolve_short_url(short_url.code) == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_uses_configured_cache_prefix(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"custom:{short_url.code}", short_url.url)

        assert resolve_short_url(short_url.code) == short_url.url

    def test_returns_url_from_db(self) -> None:
        short_url = ShortUrlFactory.create()

        assert resolve_short_url(short_url.code) == short_url.url

    def test_populates_cache_after_db_lookup(self) -> None:
        short_url = ShortUrlFactory.create()

        resolve_short_url(short_url.code)

        assert get_short_url_cache().get(f"WEE:{short_url.code}") == short_url.url

    def test_expired_code_raises(self) -> None:
        short_url = ShortUrlFactory.create(expires_at=timezone.now())

        with pytest.raises(ObjectDoesNotExist):
            resolve_short_url(short_url.code)

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(ObjectDoesNotExist):
            resolve_short_url("doesnotexist")


@pytest.mark.django_db
class TestAResolveShortUrl:
    def test_returns_url_from_cache(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"WEE:{short_url.code}", short_url.url)

        assert async_to_sync(aresolve_short_url)(short_url.code) == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_uses_configured_cache_prefix(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"custom:{short_url.code}", short_url.url)

        assert async_to_sync(aresolve_short_url)(short_url.code) == short_url.url

    def test_returns_url_from_db(self) -> None:
        short_url = ShortUrlFactory.create()

        assert async_to_sync(aresolve_short_url)(short_url.code) == short_url.url

    def test_populates_cache_after_db_lookup(self) -> None:
        short_url = ShortUrlFactory.create()

        async_to_sync(aresolve_short_url)(short_url.code)

        assert get_short_url_cache().get(f"WEE:{short_url.code}") == short_url.url

    def test_expired_code_raises(self) -> None:
        short_url = ShortUrlFactory.create(expires_at=timezone.now())

        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)(short_url.code)

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)("doesnotexist")
