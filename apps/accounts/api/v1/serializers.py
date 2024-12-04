from apps.accounts.api.base.serializers import (
    BaseChangePasswordSerializer,
    BaseEmailPasswordLoginSerializer,
    BaseUserSerializer,
    BaseProfileSerializer,
    BaseVehicleSerializer
)


class UserSerializer(BaseUserSerializer):
    pass


class EmailPasswordLoginSerializer(BaseEmailPasswordLoginSerializer):
    pass


class ChangePasswordSerializer(BaseChangePasswordSerializer):
    pass


class ProfileSerializer(BaseProfileSerializer):
    pass


class VehicleSerializer(BaseVehicleSerializer):
    pass
