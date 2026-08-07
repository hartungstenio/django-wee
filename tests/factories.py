import factory
from factory.django import DjangoModelFactory

from django_wee.models import ShortUrl


class ShortUrlFactory(DjangoModelFactory[ShortUrl]):
    url = factory.Faker("url")

    class Meta:
        model = ShortUrl
