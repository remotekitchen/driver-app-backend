from apps.billing.api.base.views import (
    BaseCancelDeliveryAPIView,
    BaseCheckAddressAPIView,
    BaseCreateDeliveryAPIView,
    BaseAvailableOrdersApiView,
    BaseAcceptOrderApiView,
    BaseDriverAssignedOrdersApiView
)


class CreateDeliveryAPIView(BaseCreateDeliveryAPIView):
    pass


class CheckAddressAPIView(BaseCheckAddressAPIView):
    pass


class CancelDeliveryAPIView(BaseCancelDeliveryAPIView):
    pass

class AvailableOrdersApiView(BaseAvailableOrdersApiView):
    pass  

class AcceptOrderApiView(BaseAcceptOrderApiView):
    pass
  
class DriverAssignedOrdersApiView(BaseDriverAssignedOrdersApiView):
    pass