from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from apps.billing.models import Delivery
from apps.core.api.base.serializers import BaseAddressSerializer


class BaseDeliverySerializer(WritableNestedModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"


class DeliveryCreateSerializer(BaseDeliverySerializer):
    pickup_address = BaseAddressSerializer()
    drop_off_address = BaseAddressSerializer()
