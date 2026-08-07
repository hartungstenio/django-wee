"""URL configuration for django-wee using the sync redirect view.

Include this module (or :mod:`django_wee.urls_async`) in your project's
``ROOT_URLCONF`` to enable short-URL redirects.
"""

from django.urls import path

from .views import redirect

app_name = "django_wee"

urlpatterns = [
    path("<str:code>/", redirect, name="redirect"),
]
