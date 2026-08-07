from collections.abc import Generator
from typing import Any

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache() -> Generator[None, Any]:
    cache.clear()
    yield
    cache.clear()
