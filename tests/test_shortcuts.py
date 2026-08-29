from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.test import override_settings
from django.utils import timezone

from django_wee._settings import get_short_url_cache
from django_wee.models import ShortUrl
from django_wee.shortcuts import acreate_short_url, aresolve_short_url, create_short_url, resolve_short_url

from .factories import ShortUrlFactory

if TYPE_CHECKING:
    from django.contrib.sites.models import Site


@pytest.mark.django_db
class TestCreateShortUrl:
    def test_persists_to_db_and_populates_cache(self, site: Site) -> None:
        short_url = create_short_url("https://example.com", site=site)
        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        assert get_short_url_cache().get(f"WEE:{persisted.code}") == "https://example.com"

    def test_suppresses_cache_errors(self, site: Site) -> None:
        cache = get_short_url_cache()

        with mock.patch.object(cache, "set", side_effect=Exception) as mock_set:
            short_url = create_short_url("https://example.com", site=site)

        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        mock_set.assert_called_once()
        assert get_short_url_cache().get(f"WEE:{persisted.code}") is None

    def test_persists_expiration(self, site: Site) -> None:
        expiration = timezone.now() + timedelta(days=1)

        create_short_url("https://example.com", expiration=expiration, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at == expiration

    def test_persists_ttl_as_int_seconds(self, site: Site) -> None:
        before = timezone.now()

        create_short_url("https://example.com", ttl=3600, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=3600) <= short_url.expires_at <= timezone.now() + timedelta(seconds=3600)

    def test_persists_ttl_as_float_seconds(self, site: Site) -> None:
        before = timezone.now()

        create_short_url("https://example.com", ttl=1.5, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=1.5) <= short_url.expires_at <= timezone.now() + timedelta(seconds=1.5)

    def test_persists_ttl_as_timedelta(self, site: Site) -> None:
        before = timezone.now()
        delta = timedelta(hours=2)

        create_short_url("https://example.com", ttl=delta, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + delta <= short_url.expires_at <= timezone.now() + delta

    def test_expiration_and_ttl_are_mutually_exclusive(self, site: Site) -> None:
        expiration = timezone.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="mutually exclusive"):
            create_short_url("https://example.com", expiration=expiration, ttl=3600, site=site)  # type: ignore[call-overload]

    def test_no_expiration_when_default_not_set(self, site: Site) -> None:
        short_url = create_short_url("https://example.com", site=site)
        assert short_url.expires_at is None

    @override_settings(WEE_DEFAULT_TTL=3600)
    def test_uses_wee_default_expiration_as_int_seconds(self, site: Site) -> None:
        before = timezone.now()

        short_url = create_short_url("https://example.com", site=site)

        assert short_url.expires_at is not None
        assert before + timedelta(seconds=3600) <= short_url.expires_at <= timezone.now() + timedelta(seconds=3600)

    @override_settings(WEE_DEFAULT_TTL=1.5)
    def test_uses_wee_default_expiration_as_float_seconds(self, site: Site) -> None:
        before = timezone.now()

        short_url = create_short_url("https://example.com", site=site)

        assert short_url.expires_at is not None
        assert before + timedelta(seconds=1.5) <= short_url.expires_at <= timezone.now() + timedelta(seconds=1.5)

    @override_settings(WEE_DEFAULT_TTL=timedelta(hours=2))
    def test_uses_wee_default_expiration_as_timedelta(self, site: Site) -> None:
        before = timezone.now()
        delta = timedelta(hours=2)

        short_url = create_short_url("https://example.com", site=site)

        assert short_url.expires_at is not None
        assert before + delta <= short_url.expires_at <= timezone.now() + delta

    def test_negative_ttl_as_seconds_raises(self, site: Site) -> None:
        with pytest.raises(ValueError, match="positive"):
            create_short_url("https://example.com", ttl=-1, site=site)

    def test_negative_ttl_as_timedelta_raises(self, site: Site) -> None:
        with pytest.raises(ValueError, match="positive"):
            create_short_url("https://example.com", ttl=timedelta(seconds=-1), site=site)

    def test_zero_ttl_as_seconds_warns(self, site: Site) -> None:
        with pytest.warns(UserWarning, match="expire immediately"):
            create_short_url("https://example.com", ttl=0, site=site)

    def test_zero_ttl_as_timedelta_warns(self, site: Site) -> None:
        with pytest.warns(UserWarning, match="expire immediately"):
            create_short_url("https://example.com", ttl=timedelta(0), site=site)

    def test_invalid_url_raises(self, site: Site) -> None:
        with pytest.raises(ValidationError):
            create_short_url("not a url", site=site)

    def test_allows_duplicate_url(self, site: Site) -> None:
        existing = ShortUrlFactory.create(site=site)
        duplicate = create_short_url(existing.url, site=site)

        assert duplicate.pk is not None
        assert duplicate.url == existing.url
        assert duplicate.pk != existing.pk

    def test_schemeless_url_defaults_to_https(self, site: Site) -> None:
        short_url = create_short_url("example.com", site=site)
        assert short_url.url == "https://example.com"

    def test_protocol_relative_url_defaults_to_https(self, site: Site) -> None:
        short_url = create_short_url("//example.com", site=site)
        assert short_url.url == "https://example.com"

    def test_relative_url_uses_current_site(self, site: Site) -> None:
        short_url = create_short_url("/s/SoMeCoDe/", site=site)
        assert short_url.url == "https://example.com/s/SoMeCoDe/"

    def test_invalid_relative_url_raises(self, site: Site) -> None:
        with pytest.raises(ValueError, match="Relative URLs must belong to the current site"):
            create_short_url("/definitely-not-a-real-route/", site=site)

    def test_absolute_foreign_url_is_allowed(self, site: Site) -> None:
        short_url = create_short_url("https://other.example.com/about/", site=site)
        assert short_url.url == "https://other.example.com/about/"

    def test_url_with_scheme_is_unchanged(self, site: Site) -> None:
        short_url = create_short_url("http://example.com", site=site)
        assert short_url.url == "http://example.com"


@pytest.mark.django_db
class TestACreateShortUrl:
    def test_persists_to_db_and_populates_cache(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("https://example.com", site=site)
        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        assert get_short_url_cache().get(f"WEE:{persisted.code}") == "https://example.com"

    def test_suppresses_cache_errors(self, site: Site) -> None:
        cache = get_short_url_cache()

        with mock.patch.object(cache, "aset", side_effect=Exception) as mock_set:
            short_url = async_to_sync(acreate_short_url)("https://example.com", site=site)

        persisted = ShortUrl.objects.get(url="https://example.com")

        assert short_url == persisted
        mock_set.assert_awaited_once()
        assert get_short_url_cache().get(f"WEE:{persisted.code}") is None

    def test_persists_expiration(self, site: Site) -> None:
        expiration = timezone.now() + timedelta(days=1)

        async_to_sync(acreate_short_url)("https://example.com", expiration=expiration, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at == expiration

    def test_persists_ttl_as_int_seconds(self, site: Site) -> None:
        before = timezone.now()

        async_to_sync(acreate_short_url)("https://example.com", ttl=3600, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=3600) <= short_url.expires_at <= timezone.now() + timedelta(seconds=3600)

    def test_persists_ttl_as_float_seconds(self, site: Site) -> None:
        before = timezone.now()

        async_to_sync(acreate_short_url)("https://example.com", ttl=1.5, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + timedelta(seconds=1.5) <= short_url.expires_at <= timezone.now() + timedelta(seconds=1.5)

    def test_persists_ttl_as_timedelta(self, site: Site) -> None:
        before = timezone.now()
        delta = timedelta(hours=2)

        async_to_sync(acreate_short_url)("https://example.com", ttl=delta, site=site)

        short_url = ShortUrl.objects.get(url="https://example.com")
        assert short_url.expires_at is not None
        assert before + delta <= short_url.expires_at <= timezone.now() + delta

    def test_expiration_and_ttl_are_mutually_exclusive(self, site: Site) -> None:
        expiration = timezone.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="mutually exclusive"):
            async_to_sync(acreate_short_url)("https://example.com", expiration=expiration, ttl=3600, site=site)

    def test_no_expiration_when_default_not_set(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("https://example.com", site=site)
        assert short_url.expires_at is None

    @override_settings(WEE_DEFAULT_TTL=3600)
    def test_uses_wee_default_expiration_as_int_seconds(self, site: Site) -> None:
        before = timezone.now()

        short_url = async_to_sync(acreate_short_url)("https://example.com", site=site)

        assert short_url.expires_at is not None
        assert before + timedelta(seconds=3600) <= short_url.expires_at <= timezone.now() + timedelta(seconds=3600)

    @override_settings(WEE_DEFAULT_TTL=1.5)
    def test_uses_wee_default_expiration_as_float_seconds(self, site: Site) -> None:
        before = timezone.now()

        short_url = async_to_sync(acreate_short_url)("https://example.com", site=site)

        assert short_url.expires_at is not None
        assert before + timedelta(seconds=1.5) <= short_url.expires_at <= timezone.now() + timedelta(seconds=1.5)

    @override_settings(WEE_DEFAULT_TTL=timedelta(hours=2))
    def test_uses_wee_default_expiration_as_timedelta(self, site: Site) -> None:
        before = timezone.now()
        delta = timedelta(hours=2)

        short_url = async_to_sync(acreate_short_url)("https://example.com", site=site)

        assert short_url.expires_at is not None
        assert before + delta <= short_url.expires_at <= timezone.now() + delta

    def test_negative_ttl_as_seconds_raises(self, site: Site) -> None:
        with pytest.raises(ValueError, match="positive"):
            async_to_sync(acreate_short_url)("https://example.com", ttl=-1, site=site)

    def test_negative_ttl_as_timedelta_raises(self, site: Site) -> None:
        with pytest.raises(ValueError, match="positive"):
            async_to_sync(acreate_short_url)("https://example.com", ttl=timedelta(seconds=-1), site=site)

    def test_zero_ttl_as_seconds_warns(self, site: Site) -> None:
        with pytest.warns(UserWarning, match="expire immediately"):
            async_to_sync(acreate_short_url)("https://example.com", ttl=0, site=site)

    def test_zero_ttl_as_timedelta_warns(self, site: Site) -> None:
        with pytest.warns(UserWarning, match="expire immediately"):
            async_to_sync(acreate_short_url)("https://example.com", ttl=timedelta(0), site=site)

    def test_invalid_url_raises(self, site: Site) -> None:
        with pytest.raises(ValidationError):
            async_to_sync(acreate_short_url)("not a url", site=site)

    def test_allows_duplicate_url(self, site: Site) -> None:
        existing = ShortUrlFactory.create(site=site)
        duplicate = async_to_sync(acreate_short_url)(existing.url, site=site)

        assert duplicate.pk is not None
        assert duplicate.url == existing.url
        assert duplicate.pk != existing.pk

    def test_schemeless_url_defaults_to_https(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("example.com", site=site)
        assert short_url.url == "https://example.com"

    def test_protocol_relative_url_defaults_to_https(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("//example.com", site=site)
        assert short_url.url == "https://example.com"

    def test_relative_url_uses_current_site(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("/s/SoMeCoDe/", site=site)
        assert short_url.url == "https://example.com/s/SoMeCoDe/"

    def test_invalid_relative_url_raises(self, site: Site) -> None:
        with pytest.raises(ValueError, match="Relative URLs must belong to the current site"):
            async_to_sync(acreate_short_url)("/definitely-not-a-real-route/", site=site)

    def test_absolute_foreign_url_is_allowed(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("https://other.example.com/about/", site=site)
        assert short_url.url == "https://other.example.com/about/"

    def test_url_with_scheme_is_unchanged(self, site: Site) -> None:
        short_url = async_to_sync(acreate_short_url)("http://example.com", site=site)
        assert short_url.url == "http://example.com"


@pytest.mark.django_db
class TestResolveShortUrl:
    def test_returns_url_from_cache(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)
        get_short_url_cache().set(f"WEE:{short_url.code}", short_url.url)

        resolved_url = resolve_short_url(short_url.code, site)

        assert resolved_url == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_uses_configured_cache_prefix(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)
        get_short_url_cache().set(f"custom:{short_url.code}", short_url.url)

        resolved_url = resolve_short_url(short_url.code, site)

        assert resolved_url == short_url.url

    def test_returns_and_caches_url_from_db(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)

        resolved_url = resolve_short_url(short_url.code, site)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_returns_and_caches_url_from_db_custom_prefix(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)

        resolved_url = resolve_short_url(short_url.code, site)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"custom:{short_url.code}") == short_url.url

    def test_suppresses_cache_errors(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)
        cache = get_short_url_cache()

        with mock.patch.multiple(
            cache,
            get=mock.Mock(side_effect=Exception),
            set=mock.Mock(side_effect=Exception),
        ):
            resolved_url = resolve_short_url(short_url.code, site)

            assert resolved_url == short_url.url
            cache.get.assert_called_once()
            cache.set.assert_called_once()

    def test_expired_code_raises(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(expires_at=timezone.now(), site=site)

        with pytest.raises(ObjectDoesNotExist):
            resolve_short_url(short_url.code, site)

    def test_unknown_code_raises(self, site: Site) -> None:
        with pytest.raises(ObjectDoesNotExist):
            resolve_short_url("doesnotexist", site)


@pytest.mark.django_db
class TestAResolveShortUrl:
    def test_returns_url_from_cache(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)
        get_short_url_cache().set(f"WEE:{short_url.code}", short_url.url)

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code, site)

        assert resolved_url == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_uses_configured_cache_prefix(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)
        get_short_url_cache().set(f"custom:{short_url.code}", short_url.url)

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code, site)

        assert resolved_url == short_url.url

    def test_returns_and_caches_url_from_db(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code, site)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"WEE:{short_url.code}") == short_url.url

    @override_settings(WEE_CACHE_PREFIX="custom")
    def test_returns_and_caches_url_from_db_custom_prefix(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)

        resolved_url = async_to_sync(aresolve_short_url)(short_url.code, site)

        assert resolved_url == short_url.url
        assert get_short_url_cache().get(f"custom:{short_url.code}") == short_url.url

    def test_suppresses_cache_errors(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(site=site)
        cache = get_short_url_cache()

        with mock.patch.multiple(
            cache,
            aget=mock.AsyncMock(side_effect=Exception),
            aset=mock.AsyncMock(side_effect=Exception),
        ):
            resolved_url = async_to_sync(aresolve_short_url)(short_url.code, site)

            assert resolved_url == short_url.url
            cache.aget.assert_awaited_once()
            cache.aset.assert_awaited_once()

    def test_expired_code_raises(self, site: Site) -> None:
        short_url = ShortUrlFactory.create(expires_at=timezone.now(), site=site)

        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)(short_url.code, site)

    def test_unknown_code_raises(self, site: Site) -> None:
        with pytest.raises(ObjectDoesNotExist):
            async_to_sync(aresolve_short_url)("doesnotexist", site)
