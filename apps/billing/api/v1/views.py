from apps.billing.api.base.views import (
    BaseCancelDeliveryAPIView,
    BaseCheckAddressAPIView,
    BaseCreateDeliveryAPIView,
)


class CreateDeliveryAPIView(BaseCreateDeliveryAPIView):
    pass


class CheckAddressAPIView(BaseCheckAddressAPIView):
    pass


class CancelDeliveryAPIView(BaseCancelDeliveryAPIView):
    pass
