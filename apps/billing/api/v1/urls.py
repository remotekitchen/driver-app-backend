from django.urls import include, path

from apps.billing.api.v1.views import CreateDeliveryAPIView

urlpatterns = [
    path("create-delivery/", CreateDeliveryAPIView.as_view()),
]
