import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from django_wee.models import ShortUrl

from .factories import ShortUrlFactory


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
