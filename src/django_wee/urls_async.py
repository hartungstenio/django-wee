"""URL configuration for django-wee using the async redirect view.

Use this module instead of :mod:`django_wee.urls` when running under an
ASGI server to take advantage of the async view implementation.
"""

from django.urls import path

from .views import aredirect

app_name = "django_wee"

urlpatterns = [
    path("<str:code>/", aredirect, name="redirect"),
]
