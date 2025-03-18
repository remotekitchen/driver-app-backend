from rest_framework import serializers
from apps.firebase.models import TokenFCM


class BaseFCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenFCM
        fields = ["id", "user", "token", "device_type"]
        extra_kwargs = {"user": {"read_only": True}}