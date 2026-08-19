from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from django_wee.models import ShortUrl

from .factories import ShortUrlFactory


@pytest.mark.django_db
class TestShortUrlQuerySet:
    def test_alive_includes_non_expiring_records(self) -> None:
        short_url = ShortUrlFactory.create(expires_at=None)

        assert list(ShortUrl.objects.alive()) == [short_url]

    def test_alive_includes_unexpired_records(self) -> None:
        expiration = timezone.now() + timedelta(days=1)
        short_url = ShortUrlFactory.create(expires_at=expiration)

        assert list(ShortUrl.objects.alive()) == [short_url]

    def test_alive_excludes_expired_records(self) -> None:
        ShortUrlFactory.create(expires_at=timezone.now() - timedelta(days=1))

        assert list(ShortUrl.objects.alive()) == []

    def test_alive_excludes_exactly_expired_records(self) -> None:
        ShortUrlFactory.create(expires_at=timezone.now())

        assert list(ShortUrl.objects.alive()) == []

    def test_alive_returns_only_alive_among_mixed_records(self) -> None:
        alive_no_expiration = ShortUrlFactory.create(expires_at=None)
        alive_future = ShortUrlFactory.create(expires_at=timezone.now() + timedelta(days=1))
        ShortUrlFactory.create(expires_at=timezone.now() - timedelta(days=1))
        ShortUrlFactory.create(expires_at=timezone.now())

        assert set(ShortUrl.objects.alive()) == {alive_no_expiration, alive_future}


@pytest.mark.django_db
class TestShortUrl:
    def test_invalid_url_raises_on_full_clean(self) -> None:
        with pytest.raises(ValidationError):
            ShortUrl(url="not-a-url").full_clean()

    def test_duplicate_url_raises_on_full_clean(self) -> None:
        existing = ShortUrlFactory.create()
        with pytest.raises(ValidationError):
            ShortUrl(url=existing.url).full_clean()

    def test_duplicate_url_raises_integrity_error_at_db_level(self) -> None:
        existing = ShortUrlFactory.create()
        with pytest.raises(IntegrityError):
            ShortUrl.objects.create(url=existing.url)
