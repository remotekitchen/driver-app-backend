from apps.billing.api.base.views import (
    BaseCancelDeliveryAPIView,
    BaseCheckAddressAPIView,
    BaseCreateDeliveryAPIView,
    BaseAvailableOrdersApiView,
    BaseAcceptOrderApiView,
    BaseDriverAssignedOrdersApiView,
    BaseOrderUpdateRetrieveApiView,
    BasePickedUpOrdersApiViews
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
  
class OrderUpdateRetrieveApiView(BaseOrderUpdateRetrieveApiView):
    pass
  
class PickedUpOrdersApiViews(BasePickedUpOrdersApiViews):
    pass