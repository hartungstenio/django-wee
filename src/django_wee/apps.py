"""AppConfig for the django-wee application."""

from django.apps import AppConfig

from ._compat import override


class DjangoWeeConfig(AppConfig):
    """Django application configuration for django-wee."""

    name = "django_wee"
    default_auto_field = "django.db.models.BigAutoField"

    @override
    def ready(self) -> None:
        from . import checks  # noqa: F401, PLC0415
