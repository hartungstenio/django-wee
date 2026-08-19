"""Views for django-wee — resolves a short code to its destination URL."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import gettext as _

from ._internal import redirect_to
from .models import ShortUrl
from .shortcuts import aresolve_short_url, resolve_short_url

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
    try:
        url = resolve_short_url(code)
    except ObjectDoesNotExist as exc:
        msg = _("No %s matches the given query.") % ShortUrl._meta.object_name
        raise Http404(msg) from exc
    else:
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
    try:
        url = await aresolve_short_url(code)
    except ObjectDoesNotExist as exc:
        msg = _("No %s matches the given query.") % ShortUrl._meta.object_name
        raise Http404(msg) from exc
    else:
        return redirect_to(url)
