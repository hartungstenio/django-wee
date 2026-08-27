import factory
from django.contrib.sites.models import Site
from factory.django import DjangoModelFactory

from django_wee.models import ShortUrl


class ShortUrlFactory(DjangoModelFactory[ShortUrl]):
    url = factory.Faker("url")  # type: ignore[attr-defined,no-untyped-call]
    site = factory.LazyFunction(Site.objects.get_current)  # type: ignore[attr-defined,no-untyped-call]

    class Meta:
        model = ShortUrl
