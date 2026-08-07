from http import HTTPStatus

import pytest
from asgiref.sync import async_to_sync
from django.http import Http404
from django.test import AsyncRequestFactory, RequestFactory

from django_wee._internal import get_short_url_cache
from django_wee.views import aredirect, redirect

from .factories import ShortUrlFactory


@pytest.mark.django_db
class TestRedirect:
    def test_redirects_to_url_from_cache(self, rf: RequestFactory) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(short_url.code, short_url.url)
        request = rf.get(f"/s/{short_url.code}/")

        response = redirect(request, code=short_url.code)

        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert response["Location"] == short_url.url

    def test_redirects_to_url_from_db(self, rf: RequestFactory) -> None:
        short_url = ShortUrlFactory.create()
        request = rf.get(f"/s/{short_url.code}/")

        response = redirect(request, code=short_url.code)

        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert response["Location"] == short_url.url

    def test_unknown_code_raises_404(self, rf: RequestFactory) -> None:
        request = rf.get("/s/doesnotexist/")

        with pytest.raises(Http404):
            redirect(request, code="doesnotexist")


@pytest.mark.django_db
class TestARedirect:
    def test_redirects_to_url_from_cache(self, async_rf: AsyncRequestFactory) -> None:
        short_url = ShortUrlFactory.create()
        get_short_url_cache().set(short_url.code, short_url.url)
        request = async_rf.get(f"/s/{short_url.code}/")

        response = async_to_sync(aredirect)(request, code=short_url.code)

        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert response["Location"] == short_url.url

    def test_redirects_to_url_from_db(self, async_rf: AsyncRequestFactory) -> None:
        short_url = ShortUrlFactory.create()
        request = async_rf.get(f"/s/{short_url.code}/")

        response = async_to_sync(aredirect)(request, code=short_url.code)

        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert response["Location"] == short_url.url

    def test_unknown_code_raises_404(self, async_rf: AsyncRequestFactory) -> None:
        request = async_rf.get("/s/doesnotexist/")

        with pytest.raises(Http404):
            async_to_sync(aredirect)(request, code="doesnotexist")
