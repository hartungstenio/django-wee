import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError

from django_wee._internal import get_short_url_cache
from django_wee.models import ShortUrl
from django_wee.shortcuts import acreate_short_url, create_short_url

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
        assert get_short_url_cache().get(short_url.code) == "https://example.com"

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
        assert get_short_url_cache().get(short_url.code) == "https://example.com"

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError):
            async_to_sync(acreate_short_url)("not-a-url")

    def test_duplicate_url_raises(self) -> None:
        existing = ShortUrlFactory.create()
        with pytest.raises(ValidationError):
            async_to_sync(acreate_short_url)(existing.url)
