from django.urls import include, path

urlpatterns = [
    path("s/", include("django_wee.urls", namespace="django_wee")),
]
