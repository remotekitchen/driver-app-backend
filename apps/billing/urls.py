from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("apps.billing.api.v1.urls")),
]
