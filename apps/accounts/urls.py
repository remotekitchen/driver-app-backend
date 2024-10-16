from django.urls import include, path

try:
    from allauth.socialaccount import providers
except ImportError:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")

urlpatterns = [
    path("", include("allauth.urls")),
    path("api/v1/", include("apps.accounts.api.v1.urls")),
]
