from apps.accounts.api.base.serializers import BaseEmailPasswordLoginSerializer
from apps.accounts.api.base.views import (
    BaseAppleLoginAPIView,
    BaseChangePasswordAPIView,
    BaseEmailPasswordLoginAPIView,
    BaseGoogleConnectAPIView,
    BaseGoogleLoginAPIView,
    BaseUserEmailVerifyView,
    BaseUserRegistrationAPIView,
    BaseUserRetrieveUpdateDestroyAPIView,
    BaseProfileAPIView,
    BaseVehicleAPIView,
    BaseDriverSessionView,
    BaseDriverStatusView,
    BaseAdminGetAllActiveDriversView,
    BaseDriverWorkHistorySummaryView,
    BaseDriverVerifyChatView
)
from apps.accounts.api.v1.serializers import ChangePasswordSerializer, UserSerializer


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



class ProfileAPIView(BaseProfileAPIView):
    pass


class VehicleAPIView(BaseVehicleAPIView):
    pass
  
class DriverSessionView(BaseDriverSessionView):
  pass

class DriverStatusView(BaseDriverStatusView):
    pass

class AdminGetAllActiveDriversView(BaseAdminGetAllActiveDriversView):
    pass
  
class DriverWorkHistorySummaryView(BaseDriverWorkHistorySummaryView):
    pass
  
class DriverVerifyChatView(BaseDriverVerifyChatView):
    pass