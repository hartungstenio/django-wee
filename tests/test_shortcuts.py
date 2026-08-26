from datetime import timedelta
from unittest import mock

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
    def test_persists_to_db_and_populates_cache(self) -> None:
        short_url = create_short_url("https://example.com")
        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        assert get_short_url_cache().get(f"WEE:{persisted.code}") == "https://example.com"

    def test_suppresses_cache_errors(self) -> None:
        cache = get_short_url_cache()

        with mock.patch.object(cache, "set", side_effect=Exception) as mock_set:
            short_url = create_short_url("https://example.com")

        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        mock_set.assert_called_once()
        assert get_short_url_cache().get(f"WEE:{persisted.code}") is None

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
            create_short_url("not a url")

    def test_allows_duplicate_url(self) -> None:
        existing = ShortUrlFactory.create()
        duplicate = create_short_url(existing.url)

        assert duplicate.pk is not None
        assert duplicate.url == existing.url
        assert duplicate.pk != existing.pk

    def test_schemeless_url_defaults_to_https(self) -> None:
        short_url = create_short_url("example.com")
        assert short_url.url == "https://example.com"

    def test_protocol_relative_url_defaults_to_https(self) -> None:
        short_url = create_short_url("//example.com")
        assert short_url.url == "https://example.com"

    def test_url_with_scheme_is_unchanged(self) -> None:
        short_url = create_short_url("http://example.com")
        assert short_url.url == "http://example.com"


@pytest.mark.django_db
class TestACreateShortUrl:
    def test_persists_to_db_and_populates_cache(self) -> None:
        short_url = async_to_sync(acreate_short_url)("https://example.com")
        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        assert get_short_url_cache().get(f"WEE:{persisted.code}") == "https://example.com"

    def test_suppresses_cache_errors(self) -> None:
        cache = get_short_url_cache()

        with mock.patch.object(cache, "aset", side_effect=Exception) as mock_set:
            short_url = async_to_sync(acreate_short_url)("https://example.com")

        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        mock_set.assert_awaited_once()
        assert get_short_url_cache().get(f"WEE:{persisted.code}") is None

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
            async_to_sync(acreate_short_url)("https://example.com", expiration=expiration, ttl=3600)  # type: ignore[call-overload]

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            async_to_sync(acreate_short_url)("not a url")

    def test_allows_duplicate_url(self) -> None:
        existing = ShortUrlFactory.create()
        duplicate = async_to_sync(acreate_short_url)(existing.url)

        assert duplicate.pk is not None
        assert duplicate.url == existing.url
        assert duplicate.pk != existing.pk

    def test_schemeless_url_defaults_to_https(self) -> None:
        short_url = async_to_sync(acreate_short_url)("example.com")
        assert short_url.url == "https://example.com"

    def test_protocol_relative_url_defaults_to_https(self) -> None:
        short_url = async_to_sync(acreate_short_url)("//example.com")
        assert short_url.url == "https://example.com"

    def test_url_with_scheme_is_unchanged(self) -> None:
        short_url = async_to_sync(acreate_short_url)("http://example.com")
        assert short_url.url == "http://example.com"


@pytest.mark.django_db
class TestResolveShortUrl:
    def test_returns_url_from_cache(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"WEE:{short_url.code}", short_url.url)

        resolved_url = resolve_short_url(short_url.code)

        assert resolved_url == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_uses_configured_cache_prefix(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"custom:{short_url.code}", short_url.url)

        resolved_url = resolve_short_url(short_url.code)

        assert resolved_url == short_url.url

    def test_returns_and_caches_url_from_db(self) -> None:
        short_url = ShortUrlFactory.create()

        resolved_url = resolve_short_url(short_url.code)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_returns_and_caches_url_from_db_custom_prefix(self) -> None:
        short_url = ShortUrlFactory.create()

        resolved_url = resolve_short_url(short_url.code)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"custom:{short_url.code}") == short_url.url

    def test_suppresses_cache_errors(self) -> None:
        short_url = ShortUrlFactory.create()
        cache = get_short_url_cache()

        with mock.patch.multiple(
            cache,
            get=mock.Mock(side_effect=Exception),
            set=mock.Mock(side_effect=Exception),
        ):
            resolved_url = resolve_short_url(short_url.code)

            assert resolved_url == short_url.url
            cache.get.assert_called_once()
            cache.set.assert_called_once()

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

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code)

        assert resolved_url == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_uses_configured_cache_prefix(self) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(f"custom:{short_url.code}", short_url.url)

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code)

        assert resolved_url == short_url.url

    def test_returns_and_caches_url_from_db(self) -> None:
        short_url = ShortUrlFactory.create()

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_returns_and_caches_url_from_db_custom_prefix(self) -> None:
        short_url = ShortUrlFactory.create()

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"custom:{short_url.code}") == short_url.url

    def test_suppresses_cache_errors(self) -> None:
        short_url = ShortUrlFactory.create()
        cache = get_short_url_cache()

        with mock.patch.multiple(
            cache,
            aget=mock.AsyncMock(side_effect=Exception),
            aset=mock.AsyncMock(side_effect=Exception),
        ):
            resolved_url = async_to_sync(aresolve_short_url)(short_url.code)

            assert resolved_url == short_url.url
            cache.aget.assert_awaited_once()
            cache.aset.assert_awaited_once()

    def test_expired_code_raises(self) -> None:
        short_url = ShortUrlFactory.create(expires_at=timezone.now())

        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)(short_url.code)

    def test_unknown_code_raises(self) -> None:
        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)("doesnotexist")
