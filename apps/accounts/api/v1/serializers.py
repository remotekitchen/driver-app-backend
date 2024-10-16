from apps.accounts.api.base.serializers import (
    BaseChangePasswordSerializer,
    BaseEmailPasswordLoginSerializer,
    BaseUserSerializer,
)


class UserSerializer(BaseUserSerializer):
    pass


class EmailPasswordLoginSerializer(BaseEmailPasswordLoginSerializer):
    pass


class ChangePasswordSerializer(BaseChangePasswordSerializer):
    pass
