from rest_framework import serializers

from apps.core.models import Address


class BaseAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
