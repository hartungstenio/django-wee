from collections.abc import Generator
from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.cache import cache

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_cache() -> Generator[None, Any]:
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def site() -> Site:
    """Get or create the default site."""
    return Site.objects.get_or_create(
        pk=1,
        defaults={"domain": "example.com", "name": "example.com"},
    )[0]
