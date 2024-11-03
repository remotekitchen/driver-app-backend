from django.urls import include, path

from apps.billing.api.v1.views import (
    CancelDeliveryAPIView,
    CheckAddressAPIView,
    CreateDeliveryAPIView,
)

urlpatterns = [
    path("create-delivery/", CreateDeliveryAPIView.as_view()),
    path("check-address/", CheckAddressAPIView.as_view()),
    path("cancel-delivery/", CancelDeliveryAPIView.as_view()),
]
