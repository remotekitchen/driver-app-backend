from django.urls import include, path

from apps.billing.api.v1.views import (
    CancelDeliveryAPIView,
    CheckAddressAPIView,
    CreateDeliveryAPIView,
    AvailableOrdersApiView,
    AcceptOrderApiView,
    DriverAssignedOrdersApiView,
    OrderUpdateRetrieveApiView,
    PickedUpOrdersApiViews,
    DriverOrderApiView,
    AdminGetAllOrdersApiView,
    DashboardSalesApiView
)

urlpatterns = [
    path("create-delivery/", CreateDeliveryAPIView.as_view()),
    path("check-address/", CheckAddressAPIView.as_view()),
    path("cancel-delivery/", CancelDeliveryAPIView.as_view()),
    path("available-deliveries/", AvailableOrdersApiView.as_view()),
    path("accept-delivery/<int:client_id>/", AcceptOrderApiView.as_view()),
    path("assigned-deliveries/", DriverAssignedOrdersApiView.as_view()),
    path("order/<int:client_id>/", OrderUpdateRetrieveApiView.as_view()),
    path("picked-up-deliveries/", PickedUpOrdersApiViews.as_view()),
    path("driver-order/", DriverOrderApiView.as_view()),
    path("admin-orders/", AdminGetAllOrdersApiView.as_view()),
    path("dashboard-sales/", DashboardSalesApiView.as_view())
]
