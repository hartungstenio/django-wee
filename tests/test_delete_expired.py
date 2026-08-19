from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from django_wee.models import ShortUrl

from .factories import ShortUrlFactory


@pytest.mark.django_db
class TestDeleteExpiredCommand:
    def test_delete_expired_deletes_all_expired_urls(self) -> None:
        expired = ShortUrlFactory.create(expires_at=timezone.now() - timedelta(days=1))
        ShortUrlFactory.create(expires_at=timezone.now() - timedelta(hours=1))

        call_command("delete_expired_short_urls")

        assert not ShortUrl.objects.filter(id__in=[expired.id]).exists()
        assert ShortUrl.objects.filter(expires_at__isnull=False).count() == 0

    def test_delete_expired_keeps_non_expiring_urls(self) -> None:
        non_expiring = ShortUrlFactory.create(expires_at=None)

        call_command("delete_expired_short_urls")

        assert ShortUrl.objects.filter(id=non_expiring.id).exists()

    def test_delete_expired_keeps_unexpired_urls(self) -> None:
        unexpired = ShortUrlFactory.create(expires_at=timezone.now() + timedelta(days=1))

        call_command("delete_expired_short_urls")

        assert ShortUrl.objects.filter(id=unexpired.id).exists()

    def test_delete_expired_deletes_exactly_expired_urls(self) -> None:
        exactly_expired = ShortUrlFactory.create(expires_at=timezone.now())

        call_command("delete_expired_short_urls")

        assert not ShortUrl.objects.filter(id=exactly_expired.id).exists()

    def test_delete_expired_older_than_deletes_only_older_urls(self) -> None:
        recently_expired = ShortUrlFactory.create(expires_at=timezone.now() - timedelta(hours=1))
        old_expired = ShortUrlFactory.create(expires_at=timezone.now() - timedelta(days=10))

        call_command("delete_expired_short_urls", older_than=timedelta(days=7))

        assert ShortUrl.objects.filter(id=recently_expired.id).exists()
        assert not ShortUrl.objects.filter(id=old_expired.id).exists()

    def test_delete_expired_older_than_keeps_non_expiring_urls(self) -> None:
        non_expiring = ShortUrlFactory.create(expires_at=None)

        call_command("delete_expired_short_urls", older_than=timedelta(days=7))

        assert ShortUrl.objects.filter(id=non_expiring.id).exists()

    def test_delete_expired_dry_run_does_not_delete(self) -> None:
        ShortUrlFactory.create(expires_at=timezone.now() - timedelta(days=1))

        call_command("delete_expired_short_urls", dry_run=True)

        assert ShortUrl.objects.filter(expires_at__isnull=False).count() == 1

    def test_delete_expired_dry_run_with_older_than_does_not_delete(self) -> None:
        ShortUrlFactory.create(expires_at=timezone.now() - timedelta(days=10))

        call_command("delete_expired_short_urls", older_than=timedelta(days=7), dry_run=True)

        assert ShortUrl.objects.filter(expires_at__isnull=False).count() == 1

    def test_delete_expired_with_no_expired_urls(self) -> None:
        expected = [
            ShortUrlFactory.create(expires_at=None),
            ShortUrlFactory.create(expires_at=timezone.now() + timedelta(days=1)),
        ]

        call_command("delete_expired_short_urls")

        assert ShortUrl.objects.count() == len(expected)
