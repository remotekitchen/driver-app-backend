from apps.accounts.api.base.serializers import (
    BaseChangePasswordSerializer,
    BaseEmailPasswordLoginSerializer,
    BaseUserSerializer,
    BaseProfileSerializer
)


class UserSerializer(BaseUserSerializer):
    pass


class EmailPasswordLoginSerializer(BaseEmailPasswordLoginSerializer):
    pass


class ChangePasswordSerializer(BaseChangePasswordSerializer):
    pass


class ProfileSerializer(BaseProfileSerializer):
    pass
