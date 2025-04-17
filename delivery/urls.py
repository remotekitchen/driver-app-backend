from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("apps.accounts.urls")),
    path("delivery/", include("apps.billing.urls")),
    path("address/", include("apps.core.urls")),
    path("firebase/", include("apps.firebase.urls")),
    path("chat/", include("apps.chat.urls")),
]
