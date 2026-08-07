"""Views for django-wee — resolves a short code to its destination URL."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import aget_object_or_404, get_object_or_404

from ._internal import get_short_url_cache, redirect_to
from .models import ShortUrl

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


def redirect(_request: HttpRequest, code: str) -> HttpResponse:
    """Resolve *code* to its destination URL and return a redirect response.

    Checks the cache first; falls back to a database lookup via
    :func:`~django.shortcuts.get_object_or_404`. The redirect type
    (permanent or temporary) is controlled by the ``WEE_PERMANENT_REDIRECT``
    setting.

    Args:
        code: The short-URL code extracted from the request path.

    Returns:
        An :class:`~django.http.HttpResponsePermanentRedirect` or
        :class:`~django.http.HttpResponseRedirect` to the original URL.

    Raises:
        Http404: If no :class:`~django_wee.models.ShortUrl` matches *code*.
    """
    cache = get_short_url_cache()
    url = cache.get(code)
    if not url:
        short_url = get_object_or_404(ShortUrl, code=code)
        url = short_url.url

    return redirect_to(url)


async def aredirect(_request: HttpRequest, code: str) -> HttpResponse:
    """Resolve *code* to its destination URL and return a redirect response.

    Async version of :func:`redirect`.

    Checks the cache first; falls back to a database lookup via
    :func:`~django.shortcuts.aget_object_or_404`. The redirect type
    (permanent or temporary) is controlled by the ``WEE_PERMANENT_REDIRECT``
    setting.

    Args:
        code: The short-URL code extracted from the request path.

    Returns:
        An :class:`~django.http.HttpResponsePermanentRedirect` or
        :class:`~django.http.HttpResponseRedirect` to the original URL.

    Raises:
        Http404: If no :class:`~django_wee.models.ShortUrl` matches *code*.
    """
    cache = get_short_url_cache()
    url = await cache.aget(code)
    if not url:
        short_url = await aget_object_or_404(ShortUrl, code=code)
        url = short_url.url

    return redirect_to(url)
