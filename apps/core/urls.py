from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.api.v1.urls")),
]