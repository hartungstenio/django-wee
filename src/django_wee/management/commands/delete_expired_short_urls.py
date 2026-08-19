"""Management command to delete expired short URLs."""

import argparse
from datetime import timedelta
from typing import cast

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone
from django.utils.dateparse import parse_duration

from django_wee._compat import override
from django_wee.models import ShortUrl


def _parse_duration(value: str) -> timedelta:
    """Parse *value* into a :class:`~datetime.timedelta`.

    Args:
        value: The duration string to parse (e.g. ``"7 days"``, ``"PT12H"``).

    Returns:
        The parsed duration.

    Raises:
        argparse.ArgumentTypeError: If *value* is not a valid duration.
    """
    duration = parse_duration(value)
    if duration is None:
        msg = f"Invalid duration: {value!r}"
        raise argparse.ArgumentTypeError(msg)
    return duration


class Command(BaseCommand):
    """Delete expired short URLs from the database.

    Without arguments, deletes every short URL whose ``expires_at``
    timestamp is in the past. Pass ``--older-than`` to restrict the
    deletion to URLs that have been expired for at least the given
    duration.
    """

    help = "Delete expired short URLs."

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments."""
        parser.add_argument(
            "--older-than",
            type=_parse_duration,
            default=None,
            help=(
                "Only delete URLs that have been expired for at least this "
                "duration (e.g. '7 days', '12 hours', 'PT30M')."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Show how many URLs would be deleted without deleting them.",
        )

    @override
    def handle(self, *args: object, **options: object) -> None:
        """Delete expired short URLs matching the criteria."""
        older_than = cast("timedelta | None", options["older_than"])
        dry_run = cast("bool", options["dry_run"])

        threshold = timezone.now() - older_than if older_than is not None else timezone.now()
        queryset = ShortUrl.objects.filter(expires_at__lte=threshold)
        count = queryset.count()

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(f"Would delete {count} expired short URL(s)."),
            )
            return

        deleted, _ = queryset.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {deleted} expired short URL(s)."),
        )
