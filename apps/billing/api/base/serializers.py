from django.contrib.auth import get_user_model
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from apps.accounts.models import Profile, Vehicle
from apps.billing.models import Delivery
from apps.core.api.base.serializers import BaseAddressSerializer

User = get_user_model()


class BaseDriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["dp", "driving_license", "is_verified"]


class BaseDriverVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["dp", "vehicle_type", "registration_number", "brand", "model_name"]


class BaseDriverSerializer(serializers.ModelSerializer):
    rider_profile = BaseDriverProfileSerializer()
    raider_vehicle = BaseDriverVehicleSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "rider_profile",
            "raider_vehicle",
        ]


class BaseDeliverySerializer(WritableNestedModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"


class DeliveryCreateSerializer(BaseDeliverySerializer):
    pickup_address = BaseAddressSerializer()
    drop_off_address = BaseAddressSerializer()


class CheckAddressSerializer(DeliveryCreateSerializer):
    class Meta(DeliveryCreateSerializer.Meta):
        extra_kwargs = {
            "client_id": {"required": False},
            "pickup_ready_at": {"required": False},
            "pickup_last_time": {"required": False},
            "drop_off_customer_name": {"required": False},
            "drop_off_last_time": {"required": False},
            "currency": {"required": False},
            "tips": {"required": False},
            "amount": {"required": False},
            "payment_type": {"required": False},
            "pickup_phone": {"required": False},
        }


class DeliveryGETSerializer(DeliveryCreateSerializer):
    driver = BaseDriverSerializer()
