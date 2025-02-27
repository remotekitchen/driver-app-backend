from django.contrib.auth import get_user_model
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from apps.accounts.models import Profile, Vehicle
from apps.billing.models import Delivery
from apps.core.api.base.serializers import BaseAddressSerializer
from django.utils import timezone

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

    def validate(self, attrs):
        # Determine the new status; if not provided in attrs, fall back to the current instance.
        new_status = attrs.get('status', self.instance.status if self.instance else None)
        # Try to get the delivery image from incoming data, or use the existing image on the instance.
        new_image = attrs.get('delivered_product_image', self.instance.delivered_product_image if self.instance else None)
        
        # If updating status to DELIVERY_SUCCESS, require an image.
        if new_status == Delivery.STATUS_TYPE.DELIVERY_SUCCESS and not new_image:
            raise serializers.ValidationError("An image is required to update the status to DELIVERY_SUCCESS.")
        
        return attrs
      
    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        
        # Automatically set cash_collected to the order amount when status is DELIVERY_SUCCESS
        if new_status == Delivery.STATUS_TYPE.DELIVERY_SUCCESS:
            validated_data['cash_collected'] = instance.amount
            validated_data['actual_delivery_completed_time'] = timezone.now()
            
        
        
        return super().update(instance, validated_data)

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


class BaseCancelDeliverySerializer(serializers.Serializer):
    uid = serializers.CharField()
    reason = serializers.CharField(required=False)
