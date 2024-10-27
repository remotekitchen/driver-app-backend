from django.contrib.auth import get_user_model
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from apps.billing.models import Delivery
from apps.core.api.base.serializers import BaseAddressSerializer

User = get_user_model()


class BaseDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "phone"]


class BaseDeliverySerializer(WritableNestedModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"


class DeliveryCreateSerializer(BaseDeliverySerializer):
    pickup_address = BaseAddressSerializer()
    drop_off_address = BaseAddressSerializer()


class DeliveryGETSerializer(DeliveryCreateSerializer):
    driver = BaseDriverSerializer()
