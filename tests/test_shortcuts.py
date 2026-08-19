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
    def test_returns_path_containing_code(self) -> None:
        path = create_short_url("https://example.com")
        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.code in path

    def test_persists_to_db_and_populates_cache(self) -> None:
        create_short_url("https://example.com")
        short_url = ShortUrl.objects.get(url="https://example.com")
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == "https://example.com"

    def test_persists_expiration(self) -> None:
        expiration = timezone.now() + timedelta(days=1)

        create_short_url("https://example.com", expiration)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at == expiration

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            create_short_url("not-a-url")

    def test_duplicate_url_raises(self) -> None:
        existing = ShortUrlFactory.create()
        with pytest.raises(ValidationError):
            create_short_url(existing.url)


@pytest.mark.django_db
class TestACreateShortUrl:
    def test_returns_path_containing_code(self) -> None:
        path = async_to_sync(acreate_short_url)("https://example.com")
        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.code in path

    def test_persists_to_db_and_populates_cache(self) -> None:
        async_to_sync(acreate_short_url)("https://example.com")
        short_url = ShortUrl.objects.get(url="https://example.com")
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == "https://example.com"

    def test_persists_expiration(self) -> None:
        expiration = timezone.now() + timedelta(days=1)

        async_to_sync(acreate_short_url)("https://example.com", expiration)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at == expiration

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

    def test_expired_code_raises(self) -> None:
        short_url = ShortUrlFactory.create(expires_at=timezone.now())

        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)(short_url.code)

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)("doesnotexist")
