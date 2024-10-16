from accounts.api.base.serializers import BaseUserSerializer, BaseEmailPasswordLoginSerializer, BaseChangePasswordSerializer, BaseRestaurantUserSerializer, BaseUserAddressSerializer


class UserSerializer(BaseUserSerializer):
    pass


class EmailPasswordLoginSerializer(BaseEmailPasswordLoginSerializer):
    pass


class ChangePasswordSerializer(BaseChangePasswordSerializer):
    pass


class RestaurantUserSerializer(BaseRestaurantUserSerializer):
    pass


class UserAddressSerializer(BaseUserAddressSerializer):
    pass
