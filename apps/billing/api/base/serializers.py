from django.contrib.auth import get_user_model
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from apps.accounts.models import Profile, Vehicle
from apps.billing.models import Delivery, DeliveryIssue
from apps.core.api.base.serializers import BaseAddressSerializer
from django.utils import timezone
from dateutil.parser import parse
import pytz
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
    time_so_far = serializers.SerializerMethodField()
    class Meta:
        model = Delivery
        fields = "__all__"
    
    def get_time_so_far(self, obj):
        pickup_last_time = getattr(obj, 'pickup_last_time', None)
        pickup_ready_at = getattr(obj, 'pickup_ready_at', None)

        if isinstance(obj, dict):
            pickup_last_time = obj.get('pickup_last_time')
            pickup_ready_at = obj.get('pickup_ready_at')

        if pickup_last_time and pickup_ready_at:
            # Convert strings to datetime if needed
            if isinstance(pickup_last_time, str):
                pickup_last_time = parse(pickup_last_time)
            if isinstance(pickup_ready_at, str):
                pickup_ready_at = parse(pickup_ready_at)

            delta = pickup_last_time - pickup_ready_at
            seconds = int(delta.total_seconds())
            if seconds < 60:
                return f"{seconds} seconds"
            return f"{seconds // 60} minutes"

        return "N/A"

            

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
            bdt = pytz.timezone('Asia/Dhaka')
            bdt_time = timezone.now().astimezone(bdt)
            validated_data['cash_collected'] = instance.amount
            validated_data['actual_delivery_completed_time'] = bdt_time
            
        
        
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

# Dynamic daily deliveries serializer item
class DailyDriverDeliverySerializer(serializers.Serializer):
    day = serializers.CharField()
    deliveries = serializers.DictField(child=serializers.IntegerField())

class DriverSummarySerializer(serializers.Serializer):
    driver_name = serializers.CharField()
    email = serializers.CharField()
    orders_delivered = serializers.IntegerField()
    weekly_growth_pct = serializers.FloatField()

class DriverDetailSerializer(serializers.Serializer):
    driver_id = serializers.CharField()
    driver_name = serializers.CharField()
    phone_number = serializers.CharField()
    email = serializers.CharField()
    status = serializers.CharField()
    days_since_joined = serializers.IntegerField()
    avg_cost_per_delivery = serializers.FloatField()
    fulfillment_rate = serializers.FloatField()
    on_time_delivery_rate = serializers.FloatField()
    total_earnings = serializers.FloatField()
    avg_earning_per_month = serializers.FloatField()

class DashboardSerializer(serializers.Serializer):
    greeting = serializers.CharField()
    admin_name = serializers.CharField()
    average_fulfillment_rate = serializers.FloatField()
    fulfillment_rate_change_pct = serializers.FloatField()
    driver_delivery_count = serializers.IntegerField()
    driver_delivery_count_change_pct = serializers.FloatField()
    daily_driver_deliveries = DailyDriverDeliverySerializer(many=True)
    driver_summary = DriverSummarySerializer(many=True)
    driver_details = DriverDetailSerializer(many=True)
    
    
    
class DeliveryIssueSerializer(serializers.ModelSerializer):
    order_id= serializers.SerializerMethodField()
    class Meta:
        model = DeliveryIssue
        fields = '__all__'
        
    def get_order_id(self, obj):
        return obj.delivery.client_id if obj.delivery else None