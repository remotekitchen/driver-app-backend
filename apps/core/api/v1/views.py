
from apps.core.api.base.views import BaseAddressApiView, BaseAddressDetailApiView
from apps.core.api.base.serializers import BaseAddressSerializer

class AddressApiView(BaseAddressApiView):
    serializer_class = BaseAddressSerializer
    
class AddressDetailApiView(BaseAddressDetailApiView):
    serializer_class = BaseAddressSerializer