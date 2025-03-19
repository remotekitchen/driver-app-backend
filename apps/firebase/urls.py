from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path("api/v1/", include("apps.firebase.api.v1.urls")),
]