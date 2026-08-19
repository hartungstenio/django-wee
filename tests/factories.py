import factory
from factory.django import DjangoModelFactory

from django_wee.models import ShortUrl


class ShortUrlFactory(DjangoModelFactory[ShortUrl]):
    url = factory.Faker("url")  # type: ignore[attr-defined,no-untyped-call]

    class Meta:
        model = ShortUrl
