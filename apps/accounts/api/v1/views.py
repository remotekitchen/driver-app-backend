from accounts.api.base.serializers import BaseEmailPasswordLoginSerializer
from accounts.api.base.views import (
    BaseAppleLoginAPIView, BaseChangePasswordAPIView, BaseContactModelAPIView,
    BaseEmailPasswordLoginAPIView, BaseGoogleConnectAPIView,
    BaseGoogleLoginAPIView, BaseRestaurantUserAPIView,
    BaseRestaurantUserRetrieveAPIView, BaseUserAddressListCreateAPIView,
    BaseUserAddressRetrieveUpdateDestroyAPIView, BaseUserEmailVerifyView,
    BaseUserRegistrationAPIView, BaseUserRetrieveUpdateDestroyAPIView)
from accounts.api.v1.serializers import (ChangePasswordSerializer,
                                         RestaurantUserSerializer,
                                         UserAddressSerializer, UserSerializer)


class UserRegistrationAPIView(BaseUserRegistrationAPIView):
    serializer_class = UserSerializer


class UserEmailVerifyView(BaseUserEmailVerifyView):
    pass


class EmailPasswordLoginAPIView(BaseEmailPasswordLoginAPIView):
    serializer_class = BaseEmailPasswordLoginSerializer


class GoogleLoginAPIView(BaseGoogleLoginAPIView):
    pass


class GoogleConnectAPIView(BaseGoogleConnectAPIView):
    pass


class AppleLoginAPIView(BaseAppleLoginAPIView):
    pass


class UserRetrieveUpdateDestroyAPIView(BaseUserRetrieveUpdateDestroyAPIView):
    pass


class ChangePasswordAPIView(BaseChangePasswordAPIView):
    serializer_class = ChangePasswordSerializer


class RestaurantUserAPIView(BaseRestaurantUserAPIView):
    pass


class RestaurantUserRetrieveAPIView(BaseRestaurantUserRetrieveAPIView):
    serializer_class = RestaurantUserSerializer


class UserAddressListCreateAPIView(BaseUserAddressListCreateAPIView):
    serializer_class = UserAddressSerializer


class UserAddressRetrieveUpdateDestroyAPIView(BaseUserAddressRetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer


class ContactModelAPIView(BaseContactModelAPIView):
    pass
