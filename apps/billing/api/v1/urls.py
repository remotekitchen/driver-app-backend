from django.urls import include, path

from apps.billing.api.v1.views import (
    CancelDeliveryAPIView,
    CheckAddressAPIView,
    CreateDeliveryAPIView,
    AvailableOrdersApiView,
    AcceptOrderApiView,
    DriverAssignedOrdersApiView,
)

urlpatterns = [
    path("create-delivery/", CreateDeliveryAPIView.as_view()),
    path("check-address/", CheckAddressAPIView.as_view()),
    path("cancel-delivery/", CancelDeliveryAPIView.as_view()),
    path("available-deliveries/", AvailableOrdersApiView.as_view()),
    path("accept-delivery/<int:client_id>/", AcceptOrderApiView.as_view()),
    path("assigned-deliveries/", DriverAssignedOrdersApiView.as_view()),
]
