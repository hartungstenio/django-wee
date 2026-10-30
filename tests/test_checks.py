from django.test import override_settings

from django_wee.checks import E001, W001, W002, W003, check_cache


class TestCacheCheck:
    @override_settings(WEE_CACHE_ALIAS="missing")
    def test_invalid_cache_alias_emits_e001(self) -> None:
        assert list(check_cache(app_configs=None, databases=None)) == [E001]

    @override_settings(
        WEE_CACHE_ALIAS="db",
        CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
            "db": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "test_db_cache"},
        },
    )
    def test_database_cache_emits_w001(self) -> None:
        assert list(check_cache(app_configs=None, databases=None)) == [W001]

    @override_settings(WEE_CACHE_ALIAS="default", WEE_CACHE_TIMEOUT=None)
    def test_none_timeout_emits_w002(self) -> None:
        assert list(check_cache(app_configs=None, databases=None)) == [W002]

    @override_settings(WEE_CACHE_ALIAS="default", WEE_CACHE_PREFIX="")
    def test_empty_cache_prefix_emits_w003(self) -> None:
        assert list(check_cache(app_configs=None, databases=None)) == [W003]

    @override_settings(
        WEE_CACHE_ALIAS="db",
        WEE_CACHE_TIMEOUT=None,
        WEE_CACHE_PREFIX="",
        CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
            "db": {"BACKEND": "django.core.cache.backends.db.DatabaseCache", "LOCATION": "test_db_cache"},
        },
    )
    def test_database_cache_and_none_timeout_and_empty_prefix_emit_multiple_warnings(self) -> None:
        assert list(check_cache(app_configs=None, databases=None)) == [W001, W002, W003]
