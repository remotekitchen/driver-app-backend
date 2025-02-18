from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.core.api.v1.views import AddressApiView, AddressDetailApiView

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("user/address/", AddressApiView.as_view(), name="address-list-create"),
    path("user/address/<int:pk>/", AddressDetailApiView.as_view(), name="address-detail"),
]
